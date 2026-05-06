from gspread.exceptions import APIError
from telebot.types import InputFile, InlineKeyboardMarkup, InlineKeyboardButton, MessageEntity
from io import BytesIO
from datetime import datetime, date, time, timedelta
from time import sleep
import typing as t

import json
import logging
import segno
import gspread

from web.settings import bot, DATE_FORMAT, TIME_SHORT_FORMAT, GOOGLE_KEY_PATH
from .scheduler import scheduler
from .models import Ticket
from enums import NoticeKey, Key, UserCB, book_status_dict


def generate_and_sand_qr(chat_id: int, qr_data: str, caption: str = None) -> str:
    qr = segno.make_qr(qr_data, error="H")

    buffer = BytesIO()
    qr.save(buffer, kind="png", scale=12, dark='green')
    buffer.seek(0)

    input_file = InputFile(buffer, file_name=f"{qr_data}.png")
    message = bot.send_photo(chat_id=chat_id, photo=input_file, caption=caption)
    return message.photo[-1].file_id


def get_ticket_text(ticket: Ticket) -> str:
        date_event = ticket.event.date_event.strftime(DATE_FORMAT)
        time_event = ticket.event.time_event.strftime(TIME_SHORT_FORMAT)

        return (
            f'#{ticket.id}\n'
            f'<b>{ticket.event.name}\n'
            f'📍 {ticket.event.venue.name}\n'
            f'⏰ {date_event} {time_event}\n'
            f'🪑 {ticket.option.name}</b>\n'
            f'📎 Статус: {book_status_dict.get(ticket.status, "нд")}\n'

        ).replace('None', '')


# Показать кр-код
def get_view_qr_kb(book_type: str, entry_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        keyboard=[
            [InlineKeyboardButton(
                text='🎫 Посмотреть QR-код',
                callback_data=f'{UserCB.VIEW_QR.value}:{book_type}:{entry_id}'
            )]
        ]
    )


def notice_book_for_day(entry_id: int):
    ticket = Ticket.get_by_id(entry_id)

    if ticket and ticket.is_active:
        time_str = ticket.event.time_event.strftime(TIME_SHORT_FORMAT)
        text = f'Напоминаем о мероприятии {ticket.event.name} завтра в {time_str} в {ticket.event.venue.name}'
        bot.send_message(chat_id=ticket.user_id, text=text)


# предупреждаем за 3 часа
def notice_book_for_2_hours(entry_id: int):
    ticket = Ticket.get_by_id(entry_id)

    if ticket and ticket.is_active:
        text = f'Ждём вас через 2 часа в {ticket.event.venue.name} на {ticket.event.name}'
        bot.send_message(
            chat_id=ticket.user_id,
            text=text,
            reply_markup=get_view_qr_kb(book_type=Key.QR_TICKET.value, entry_id=ticket.id))


# предупреждаем об опоздании
def notice_book_for_now(entry_id: int):
    ticket = Ticket.get_by_id(entry_id)

    if ticket and ticket.is_active:
        text = f'Мы уже начали!! Ждём вас в {ticket.event.venue.name} на {ticket.event.name}'
        bot.send_message(
            chat_id=ticket.user_id,
            text=text,
            reply_markup=get_view_qr_kb(book_type=Key.QR_TICKET.value, entry_id=ticket.id))


# создаём уведомления для каждого напоминания
def create_book_notice(book_id: int, book_date: date, book_time: time):  # не удалять end_date
    now = datetime.now()
    book_dt = datetime.combine(book_date, book_time)
    logging.warning(f'now: {now}')

    book_dt_for_day = book_dt - timedelta(days=1)
    # book_dt_for_day = now + timedelta(minutes=1)
    # logging.warning(f'book_dt_for_day: {book_dt_for_day}')
    # logging.warning(f'book_dt_for_day < now: {book_dt_for_day < now}')

    if book_dt_for_day > now:
        scheduler.add_job(
            func=notice_book_for_day,
            trigger='date',
            run_date=book_dt_for_day,
            id=f"{book_id}-{Key.QR_TICKET.value}-{NoticeKey.BOOK_DAY.value}",
            args=[book_id,],
            replace_existing=True,
        )

    book_dt_for_2_hours = book_dt - timedelta(hours=2)
    # book_dt_for_2_hours = now + timedelta(minutes=2)

    if book_dt_for_2_hours > now:
        scheduler.add_job(
            func=notice_book_for_2_hours,
            trigger='date',
            run_date=book_dt_for_2_hours,
            id=f"{book_id}-{Key.QR_TICKET.value}-{NoticeKey.BOOK_2_HOUR.value}",
            args=[book_id,],
            replace_existing=True,
        )

    # book_dt = now + timedelta(minutes=3)

    scheduler.add_job(
        func=notice_book_for_now,
        trigger='date',
        run_date=book_dt,
        id=f"{book_id}-{Key.QR_TICKET.value}-{NoticeKey.BOOK_NOW.value}",
        args=[book_id,],
        replace_existing=True,
    )


def update_book_status_gs(
        spreadsheet_id: str,
        sheet_name: str,
        status: str,
        row: int,
) -> None:
    gc = gspread.service_account(filename=GOOGLE_KEY_PATH)

    spreadsheet = gc.open_by_key(spreadsheet_id)
    if str(sheet_name).isdigit():
        worksheet = spreadsheet.get_worksheet_by_id(int(sheet_name))
    else:
        worksheet = spreadsheet.worksheet(sheet_name)

    new_values = [[book_status_dict.get(status)]]

    cell_range = f"K{row}"

    max_retries = 10
    pause_sec = 2

    for attempt in range(max_retries):
        try:
            return worksheet.update(cell_range, new_values)
        except APIError as e:
            if "Quota exceeded" in str(e):
                print(f"Превышена квота, попытка {attempt+1}/{max_retries}, жду {pause_sec} сек...")
                sleep(pause_sec)
            else:
                raise  # другие ошибки не глотаем
    raise Exception("Превышен лимит попыток записи в Google Sheets")


# восстанавливает сущности
def recover_entities(entities_str: t.Optional[str]) -> list[MessageEntity]:
    if not entities_str:
        return []

    entities_list = []
    entities: list[dict] = json.loads(entities_str)
    if entities:
        for entity in entities:
            entities_list.append(MessageEntity(**entity))

    return entities_list
