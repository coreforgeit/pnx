from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, date, time, timedelta

import keyboards as kb
from init import scheduler, bot
from settings import log_error
from .text_utils import get_ticket_text, get_book_text
from google_api import add_ticket_row_to_registration, update_book_status_gs
from db import User, Book, Ticket
from data import texts_dict
from enums import NoticeKey, BookStatus, Key


# запускает планировщики
async def start_schedulers():
    scheduler.start()


# тормозит планировщики
async def shutdown_schedulers():
    scheduler.shutdown()


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
    now = datetime.now()
    book_dt = datetime.combine(book_date, book_time)

    book_dt_for_day = book_dt - timedelta(days=1)
    if book_dt_for_day < now:
        scheduler.add_job(
            func=notice_book_for_day,
            trigger='date',
            run_date=book_dt_for_day,
            id=f"{book_id}-{NoticeKey.BOOK_DAY.value}",
            args=[book_id, book_type],
            replace_existing=True,
        )

    book_dt_for_2_hours = book_dt - timedelta(hours=2)
    if book_dt_for_2_hours < now:
        scheduler.add_job(
            func=notice_book_for_2_hours,
            trigger='date',
            run_date=book_dt_for_2_hours,
            id=f"{book_id}-{NoticeKey.BOOK_2_HOUR.value}",
            args=[book_id, book_type],
            replace_existing=True,
        )

    scheduler.add_job(
        func=notice_book_for_now,
        trigger='date',
        run_date=book_dt,
        id=f"{book_id}-{NoticeKey.BOOK_NOW.value}",
        args=[book_id, book_type],
        replace_existing=True,
    )

    book_dt_for_close = book_dt + timedelta(minutes=30)
    scheduler.add_job(
        func=notice_book_for_close,
        trigger='date',
        run_date=book_dt_for_close,
        id=f"{book_id}-{NoticeKey.BOOK_CLOSE.value}",
        args=[book_id, book_type],
        replace_existing=True,
    )


# обнуляет старые билеты
async def cancel_unpaid_tickets(user_id: int, ticket_id_list: list[int]) -> None:
    for ticket_id in ticket_id_list:
        ticket = await Ticket.get_full_ticket(ticket_id)
        user = await User.get_by_id(user_id)
        if ticket.status == BookStatus.NEW.value:
            await Ticket.update(ticket_id=ticket.id, status=BookStatus.CANCELED.value, is_active=False)

            ticket_text = get_ticket_text(ticket)

            # await add_ticket_row_to_registration(
            #     spreadsheet_id=ticket.event.venue.event_gs_id,
            #     page_id=ticket.event.gs_page,
            #     ticket_id=ticket_id,
            #     option_name=ticket.option.name,
            #     user_name=user.full_name,
            #     ticket_row=ticket.gs_row
            # )

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
    now = datetime.now()
    notice_time = now - timedelta(hours=12)

    key = '-'.join(map(str, ticket_id_list))

    scheduler.add_job(
        func=notice_book_for_day,
        trigger='date',
        run_date=notice_time,
        id=f"{NoticeKey.BOOK_DAY.value}-{key}",
        args=[user_id, ticket_id_list],
        replace_existing=True,
    )
