import segno
import os
import random
from aiogram.types import FSInputFile, BufferedInputFile

from PIL import Image
from io import BytesIO
from pyzbar.pyzbar import decode

import db
import utils as ut
from init import bot
from settings import conf
from google_api import update_book_status_gs
from enums import Key, BookStatus, AdminAction


async def generate_and_sand_qr(
        chat_id: int,
        qr_type: str,
        qr_id: int,
        caption: str = None
) -> str:
    # qr_data = f'{conf.bot_link}{Key.QR.value}&{qr_type}&{chat_id}&{qr_id}'
    qr_data = f'{conf.bot_link}{Key.QR.value}-{qr_type}-{chat_id}-{qr_id}'

    qr = segno.make_qr(qr_data, error="H")

    buffer = BytesIO()
    qr.save(buffer, kind="png", scale=12, dark='green')
    buffer.seek(0)

    photo = BufferedInputFile(file=buffer.read(), filename=f'{qr_data}.png')
    sent = await bot.send_photo(chat_id=chat_id, photo=photo, caption=caption)
    return sent.photo[-1].file_id


# Распознаёт QR-код из байтового изображения.
def decode_qr_from_bytes(data: bytes) -> str | None:
    try:
        img = Image.open(BytesIO(data))
        qr_codes = decode(img)
        if qr_codes:
            return qr_codes[0].data.decode('utf-8')

    except Exception as e:
        print("Ошибка при чтении QR:", e)
    return None


async def qr_checking(user_id: int, key: str, entry_id_str: str):

    if key == Key.QR_BOOK.value:
        ticket_id = int(entry_id_str)

        book = await db.Book.get_booking_with_venue(ticket_id)

        if not book:
            # await msg.answer("❌ Бронь не найдена")
            await bot.send_message(user_id, "❌ Бронь не найдена")

            return

        if book.status != BookStatus.CONFIRMED.value:
            # await msg.answer("❌ Уже была использована")
            await bot.send_message(user_id, "❌ Уже была использована")

            return

        if not book.is_active:
            # await msg.answer("❌ Уже была отменена")
            await bot.send_message(user_id, "❌ Уже была отменена")

            return

        book_text = ut.get_book_text(book)
        # await msg.answer(f"✅ Бронь подтверждена\n\n{book_text}")
        await bot.send_message(user_id, f"✅ Бронь подтверждена\n\n{book_text}")

        await bot.send_message(
            chat_id=book.user_id, text=f'✅ Ваша бронь подтверждена\n\n{book_text}\n\nДобро пожаловать!'
        )

        await db.Book.update(book_id=book.id, status=BookStatus.VISITED.value, is_active=False)

        await update_book_status_gs(
            spreadsheet_id=book.venue.book_gs_id,
            sheet_name=book.date_str(),
            status=BookStatus.VISITED.value,
            row=book.gs_row,
            book_type=Key.QR_BOOK.value
        )

        # запись в журнал
        await db.AdminLog.add(
            admin_id=user_id, action=AdminAction.BOOK.value, user_id=book.user_id, comment=book_text
        )

    if key == Key.QR_TICKET.value:
        ticket_id = int(entry_id_str)

        ticket = await db.Ticket.get_full_ticket(ticket_id)

        if not ticket:
            # await msg.answer("❌ Билет не найдена")
            await bot.send_message(user_id, "❌ Билет не найден")
            return

        if ticket.status != BookStatus.CONFIRMED.value:
            # await msg.answer("❌ Уже была использована")
            await bot.send_message(user_id, "❌ Уже был использован")
            return

        if not ticket.is_active:
            # await msg.answer("❌ Билет не активен")
            await bot.send_message(user_id, "❌ Билет не активен")
            return

        ticket_text = ut.get_ticket_text(ticket)
        # await msg.answer(f"✅ Билет подтверждена\n\n{ticket_text}")
        await bot.send_message(user_id, f"✅ Билет подтверждена\n\n{ticket_text}")
        await bot.send_message(
            chat_id=ticket.user_id, text=f'✅ Ваш билет подтвержден\n\n{ticket_text}\nДобро пожаловать!'
        )

        await db.Ticket.update(ticket_id=ticket.id, status=BookStatus.VISITED.value)

        await update_book_status_gs(
            spreadsheet_id=ticket.event.venue.event_gs_id,
            sheet_name=ticket.event.gs_page,
            status=BookStatus.VISITED.value,
            row=ticket.gs_row,
            book_type=Key.QR_TICKET.value
        )

        # запись в журнал
        await db.AdminLog.add(
            admin_id=user_id, action=AdminAction.TICKET.value, user_id=ticket.user_id, comment=ticket_text
        )