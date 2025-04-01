from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, date, time, timedelta

import keyboards as kb
from init import scheduler, bot
from settings import log_error
from db import User, Book
from data import texts_dict
from enums import NoticeKey


# запускает планировщики
async def start_schedulers():
    scheduler.start()


# тормозит планировщики
async def shutdown_schedulers():
    scheduler.shutdown()


# предупреждаем за день
async def notice_book_for_day(book_id: int):
    book = await Book.get_booking_with_venue(book_id)

    if book and book.is_active:
        text = f'Напоминаем о брони {book.date_book_str()} в {book.time_book_str()} в {book.venue.name}'
        await bot.send_message(chat_id=book.user_id, text=text)


# предупреждаем за 3 часа
async def notice_book_for_2_hours(book_id):
    book = await Book.get_booking_with_venue(book_id)

    if book and book.is_active and not book.is_come:
        text = f'Ждём вас через 2 часа в {book.venue.name}'
        await bot.send_message(chat_id=book.user_id, text=text, reply_markup=kb.get_view_qr_kb(book.qr_id))


# предупреждаем об опоздании
async def notice_book_for_now(book_id: int):
    book = await Book.get_booking_with_venue(book_id)

    if book and book.is_active and not book.is_come:
        text = f'Ваша бронь активна, мы будем ждать вас ещё 30 минут в {book.venue.name}'
        await bot.send_message(chat_id=book.user_id, text=text, reply_markup=kb.get_view_qr_kb(book.qr_id))


# предупреждаем об опоздании
async def notice_book_for_close(book_id: int):
    book = await Book.get_booking_with_venue(book_id)

    if book and book.is_active and not book.is_come:
        text = f'Мы не дождались вас 😔 Простите, но бронь была снята.'
        await bot.send_message(chat_id=book.user_id, text=text)

        await Book.update(book_id=book_id, is_active=False)


# создаём уведомления для каждого напоминания
def create_book_notice(book_id: int, book_date: date, book_time: time):  # не удалять end_date
    # end_date = datetime.now() + timedelta(minutes=6)

    now = datetime.now()
    book_dt = datetime.combine(book_date, book_time)

    book_dt_for_day = book_dt - timedelta(days=1)
    if book_dt_for_day < now:
        scheduler.add_job(
            func=notice_book_for_day,
            trigger='date',
            run_date=book_dt_for_day,
            id=f"{book_id}-{NoticeKey.BOOK_DAY.value}",
            args=[book_id],
            replace_existing=True,
        )

    book_dt_for_2_hours = book_dt - timedelta(hours=2)
    if book_dt_for_2_hours < now:
        scheduler.add_job(
            func=notice_book_for_2_hours,
            trigger='date',
            run_date=book_dt_for_2_hours,
            id=f"{book_id}-{NoticeKey.BOOK_2_HOUR.value}",
            args=[book_id],
            replace_existing=True,
        )

    scheduler.add_job(
        func=notice_book_for_now,
        trigger='date',
        run_date=book_dt,
        id=f"{book_id}-{NoticeKey.BOOK_NOW.value}",
        args=[book_id],
        replace_existing=True,
    )

    book_dt_for_close = book_dt + timedelta(minutes=30)
    scheduler.add_job(
        func=notice_book_for_close,
        trigger='date',
        run_date=book_dt_for_close,
        id=f"{book_id}-{NoticeKey.BOOK_CLOSE.value}",
        args=[book_id],
        replace_existing=True,
    )
