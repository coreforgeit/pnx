from db import Book, Ticket


def get_book_text(book: Book) -> str:
    return (
        f'#{book.id}\n'
        f'<b>{book.venue.name}</b>\n'
        f'{book.date_str()} {book.time_str()} на {book.people_count} чел.\n'
        f''
        f'<i>{book.comment}</i>'
    ).replace('None', '')


def get_ticket_text(ticket: Ticket) -> str:
    return (
        f'#{ticket.id}\n'
        f'<b>{ticket.event.name}\n'
        f'📍 {ticket.event.venue.name}\n'
        f'⏰ {ticket.event.date_str()} {ticket.event.time_str()}\n'
        f'🪑 {ticket.option.name}</b>\n'
    ).replace('None', '')
    # return (
    #     f'<b>{ticket.event.venue.name}</b>\n'
    #     f'<b>{ticket.event.name}</b>\n'
    #     f'{ticket.event.date_str()} {ticket.event.time_str()} {ticket.option.name} чел.\n'
    # ).replace('None', '')
