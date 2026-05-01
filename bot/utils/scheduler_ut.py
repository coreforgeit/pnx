from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, date, time, timedelta

import keyboards as kb
from init import scheduler, bot, redis_client_1
from settings import log_error, conf
from .text_utils import get_ticket_text, get_book_text
from .payment_ut import get_pay_token
from .redis_ut import save_pay_token_redis
from google_api import update_book_status_gs
from db import User, Book, Ticket, Event
from data import texts_dict
from enums import NoticeKey, BookStatus, Key


# запускает планировщики
async def start_schedulers():
    # scheduler.add_job(
    #     func=update_pay_token,
    #     trigger=CronTrigger(hour=5),
    #     id=Key.PAY_TOKEN.value,
    #     replace_existing=True,
    # )

    # scheduler.add_job(
    #     func=print_scheduled_jobs,
    #     trigger=IntervalTrigger(hours=1),
    #     id='print_scheduled_jobs',
    #     replace_existing=True,
    # )
    scheduler.start()
    await update_pay_token()
    print_scheduled_jobs()


# тормозит планировщики
async def shutdown_schedulers():
    # scheduler.remove_job(job_id=Key.PAY_TOKEN.value)
    # scheduler.remove_job(job_id='print_scheduled_jobs')
    scheduler.shutdown()


# показывает все запланированные работ
def print_scheduled_jobs():
    jobs = scheduler.get_jobs()
    s_log = [f"\nЗапланировано {len(jobs)} задач(и):"]

    for job in jobs:
        redis_key = f'apscheduler.jobs'  # основной ключ, где хранятся job'ы
        ttl = redis_client_1.ttl(redis_key)

        s_log.append(f"- ID: {job.id}")
        s_log.append(f"  Функция: {job.func_ref}")
        s_log.append(f"  Триггер: {job.trigger}")
        s_log.append(f"  Следующий запуск: {job.next_run_time}")
        s_log.append(f"  TTL ключа jobs: {ttl if ttl >= 0 else '∞'} секунд")
        s_log.append("—" * 10)

    log_error('\n'.join(s_log), wt=False)


# предупреждаем за день
async def notice_book_for_day(entry_id: int, book_type: str):
    if book_type == Key.QR_BOOK.value:
        book = await Book.get_booking_with_venue(entry_id)

        if book and book.is_active:
            text = f'Напоминаем о брони {book.date_str()} в {book.time_str()} в {book.venue.name}'
            await bot.send_message(chat_id=book.user_id, text=text)

    elif book_type == Key.QR_TICKET.value:
        ticket = await Ticket.get_full_ticket(entry_id)

        if ticket and ticket.is_active:
            text = f'Напоминаем о мероприятии {ticket.event.name} завтра в {ticket.event.time_str()} в {ticket.event.venue.name}'
            await bot.send_message(chat_id=ticket.user_id, text=text)


# предупреждаем за 3 часа
async def notice_book_for_2_hours(entry_id: int, book_type: str):
    if book_type == Key.QR_BOOK.value:
        book = await Book.get_booking_with_venue(entry_id)

        if book and book.is_active and book.status == BookStatus.CONFIRMED.value:
            text = f'Ждём вас через 2 часа в {book.venue.name}'
            await bot.send_message(
                chat_id=book.user_id,
                text=text,
                reply_markup=kb.get_view_qr_kb(book_type=Key.QR_BOOK.value, entry_id=book.id)
            )

    elif book_type == Key.QR_TICKET.value:
        ticket = await Ticket.get_full_ticket(entry_id)

        if ticket and ticket.is_active:
            text = f'Ждём вас через 2 часа в {ticket.event.venue.name} на {ticket.event.name}'
            await bot.send_message(
                chat_id=ticket.user_id,
                text=text,
                reply_markup=kb.get_view_qr_kb(book_type=Key.QR_TICKET.value, entry_id=ticket.id))


# предупреждаем об опоздании
async def notice_book_for_now(entry_id: int, book_type: str):
    if book_type == Key.QR_BOOK.value:
        book = await Book.get_booking_with_venue(entry_id)

        if book and book.is_active and book.status == BookStatus.CONFIRMED.value:
            text = f'Ваша бронь активна, мы будем ждать вас ещё 30 минут в {book.venue.name}'
            await bot.send_message(
                chat_id=book.user_id,
                text=text,
                reply_markup=kb.get_view_qr_kb(book_type=Key.QR_BOOK.value, entry_id=book.id)
            )

    elif book_type == Key.QR_TICKET.value:
        ticket = await Ticket.get_full_ticket(entry_id)

        if ticket and ticket.is_active:
            text = f'Мы уже начали!! Ждём вас в {ticket.event.venue.name} на {ticket.event.name}'
            await bot.send_message(
                chat_id=ticket.user_id,
                text=text,
                reply_markup=kb.get_view_qr_kb(book_type=Key.QR_TICKET.value, entry_id=ticket.id))


# предупреждаем об опоздании
async def notice_book_for_close(entry_id: int, book_type: str):
    if book_type == Key.QR_BOOK.value:

        book = await Book.get_booking_with_venue(entry_id)
        if book and book.is_active and not book.status == BookStatus.CONFIRMED.value:
            text = f'Мы не дождались вас 😔 Простите, но бронь была снята.'
            await bot.send_message(chat_id=book.user_id, text=text)

            await Book.update(book_id=entry_id, is_active=False, status=BookStatus.CANCELED.value)

            await update_book_status_gs(
                spreadsheet_id=book.venue.book_gs_id,
                sheet_name=book.date_str(),
                status=BookStatus.CANCELED.value,
                row=book.gs_row,
                book_type=Key.QR_BOOK.value
            )


# создаём уведомления для каждого напоминания
def create_book_notice(book_id: int, book_date: date, book_time: time, book_type: str):  # не удалять end_date
    now = datetime.now().replace(tzinfo=conf.tz)
    book_log = [f'now {now}',]
    book_dt = datetime.combine(book_date, book_time, conf.tz)
    book_log.append(f'book_dt {book_dt} ')

    book_dt_for_day = book_dt - timedelta(days=1)
    book_log.append(f'book_dt_for_day {book_dt_for_day} | {book_dt_for_day > now}')
    if book_dt_for_day > now:
        scheduler.add_job(
            func=notice_book_for_day,
            trigger='date',
            run_date=book_dt_for_day,
            id=f"{book_id}-{book_type}-{NoticeKey.BOOK_DAY.value}",
            args=[book_id, book_type],
            replace_existing=True,
        )

    book_dt_for_2_hours = book_dt - timedelta(hours=2)
    book_log.append(f'book_dt_for_2_hours {book_dt_for_2_hours} | {book_dt_for_2_hours > now}')

    if book_dt_for_2_hours > now:
        scheduler.add_job(
            func=notice_book_for_2_hours,
            trigger='date',
            run_date=book_dt_for_2_hours,
            id=f"{book_id}-{book_type}-{NoticeKey.BOOK_2_HOUR.value}",
            args=[book_id, book_type],
            replace_existing=True,
        )

    scheduler.add_job(
        func=notice_book_for_now,
        trigger='date',
        run_date=book_dt,
        id=f"{book_id}-{book_type}-{NoticeKey.BOOK_NOW.value}",
        args=[book_id, book_type],
        replace_existing=True,
    )

    book_dt_for_close = book_dt + timedelta(minutes=30)
    book_log.append(f'book_dt_for_close {book_dt_for_close}')

    scheduler.add_job(
        func=notice_book_for_close,
        trigger='date',
        run_date=book_dt_for_close,
        id=f"{book_id}-{book_type}-{NoticeKey.BOOK_CLOSE.value}",
        args=[book_id, book_type],
        replace_existing=True,
    )

    log_error('\n'.join(book_log), wt=False)
    # print_scheduled_jobs()


'''
now 2025-05-19 15:31:27.574335
book_dt 2025-05-27 15:00:00
book_dt_for_day 2025-05-26 15:00:00 | False
book_dt_for_2_hours 2025-05-27 13:00:00 | False
book_dt_for_close 2025-05-27 15:30:00
'''


# обнуляет старые билеты
async def cancel_unpaid_tickets(user_id: int, ticket_id_list: list[int]) -> None:
    for ticket_id in ticket_id_list:
        ticket = await Ticket.get_full_ticket(ticket_id)
        # user = await User.get_by_id(user_id)
        if ticket.status == BookStatus.NEW.value:
            await Ticket.update(ticket_id=ticket.id, status=BookStatus.CANCELED.value, is_active=False)

            ticket_text = get_ticket_text(ticket)

            await update_book_status_gs(
                spreadsheet_id=ticket.event.venue.event_gs_id,
                sheet_name=ticket.event.gs_page,
                status=BookStatus.CANCELED.value,
                row=ticket.gs_row,
                book_type=Key.QR_TICKET.value
            )

            text = f'Оплата не была подтверждена, билет аннулирован\n{ticket_text}'
            await bot.send_message(chat_id=user_id, text=text)


# создаём уведомления для каждого напоминания
def create_cancel_ticket(user_id: int, ticket_id_list: list[int]):
    now = datetime.now().replace(tzinfo=conf.tz)
    notice_time = now + timedelta(hours=1)

    key = '-'.join(map(str, ticket_id_list))

    scheduler.add_job(
        func=cancel_unpaid_tickets,
        trigger='date',
        run_date=notice_time,
        id=f"{NoticeKey.BOOK_DAY.value}-{key}",
        args=[user_id, ticket_id_list],
        replace_existing=True,
    )


async def update_pay_token():
    token = await get_pay_token()
    if token:
        save_pay_token_redis(token)
        log_error(f"Токен обновлён при запуске:\n{token}", wt=False)
    else:
        log_error(f"Токен не обновлён", wt=False)


async def deactivate_event(event_id: int):
    await Event.update(event_id=event_id, is_active=False)


# создаём уведомления для каждого напоминания
def create_deactivate_event(event_id: int, event_date: date, event_time: time):
    event_dt = datetime.combine(event_date, event_time)
    run_time = event_dt + timedelta(hours=2)

    scheduler.add_job(
        func=deactivate_event,
        trigger='date',
        run_date=run_time,
        id=f"{NoticeKey.DEACTIVATE_EVENT.value}-{event_id}",
        args=[event_id,],
        replace_existing=True,
    )
