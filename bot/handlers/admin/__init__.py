from .manage_event import admin_router
from .update_event import admin_router
from .view_books_and_tickets import admin_router
from .mailing import admin_router
from .add_admin import admin_router
from .check_qr import admin_router

__all__ = ['admin_router']
