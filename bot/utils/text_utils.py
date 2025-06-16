from db import Book, Ticket

from enums import book_status_dict


def get_book_text(book: Book) -> str:
    print(f'ticket.user: {book.user}')
    full_name_row = f'{book.user.full_name} @{book.user.username}' if book.user.username else f'{book.user.full_name}'

    return (
        f'#{book.id}\n'
        f'{full_name_row}\n'
        f'<b>{book.venue.name}</b>\n'
        f'{book.date_str()} {book.time_str()} на {book.people_count} чел.\n'
        f'📎 Статус: {book_status_dict.get(book.status, "нд")}\n'
        f'<i>{book.comment}</i>'
    ).replace('None', '')


def get_ticket_text(ticket: Ticket) -> str:
    if not ticket.user:
        full_name_row = 'нд'
    else:
        full_name_row = \
            f'{ticket.user.full_name} @{ticket.user.username}' if ticket.user.username else f'{ticket.user.full_name}'
    return (
        f'#{ticket.id}\n'
        f'{full_name_row}'
        f'<b>{ticket.event.name}\n'
        f'📍 {ticket.event.venue.name}\n'
        f'⏰ {ticket.event.date_str()} {ticket.event.time_str()}\n'
        f'🪑 {ticket.option.name}</b>\n'
        f'📎 Статус: {book_status_dict.get(ticket.status, "нд")}\n'

    ).replace('None', '')
    # return (
    #     f'<b>{ticket.event.venue.name}</b>\n'
    #     f'<b>{ticket.event.name}</b>\n'
    #     f'{ticket.event.date_str()} {ticket.event.time_str()} {ticket.option.name} чел.\n'
    # ).replace('None', '')
