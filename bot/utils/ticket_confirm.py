import utils as ut
from db import Ticket
from init import user_router, bot
from google_api import update_book_status_gs
from enums import UserCB, BookStatus, TicketData, TicketStep, ticket_text_dict, UserState, Action, Key


async def confirm_tickets(user_id: int, full_name: str, ticket_id_list: list[int]):
    ticket_id = 0
    ticket = None
    for ticket_id in ticket_id_list:
        ticket = await Ticket.get_full_ticket(ticket_id)
        # qr_data = f'{Key.QR_TICKET.value}:{user_id}:{ticket_id}'
        text = ut.get_ticket_text(ticket)
        # сохраняем кр
        qr_photo_id = await ut.generate_and_sand_qr(
            chat_id=user_id,
            qr_type=Key.QR_TICKET.value,
            qr_id=ticket_id,
            caption=text
        )

        await update_book_status_gs(
            spreadsheet_id=ticket.event.venue.event_gs_id,
            sheet_name=ticket.event.gs_page,
            status=BookStatus.CONFIRMED.value,
            row=ticket.gs_row,
            book_type=Key.QR_TICKET.value
        )

        await Ticket.update(ticket_id=ticket_id, qr_id=qr_photo_id, status=BookStatus.CONFIRMED.value, is_active=True)

        text = f'<b>Подтверждён билета на {ticket.event.name} пользователь {full_name}</b>'
        await bot.send_message(chat_id=ticket.event.venue.admin_chat_id, text=text)

    if ticket_id and ticket:
        ut.create_book_notice(
            book_id=ticket_id,
            book_date=ticket.event.date_event,
            book_time=ticket.event.time_event,
            book_type=Key.QR_TICKET.value
        )
