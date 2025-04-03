from db import Book


def get_book_text(book: Book) -> str:
    return (
        f'{book.date_book_str()} {book.time_book_str()} на {book.people_count} чел.\n'
        f'<i>{book.comment}</i>'
    )
