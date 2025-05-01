from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import User, Venue, Book, Event, EventOption, Ticket, AdminLog, LogError, Payment


@admin.register(User)
class UserAdmin(ModelAdmin):
    list_display = ('id', 'full_name', 'username', 'status', 'mailing', 'venue', 'last_visit')
    list_filter = ('status', 'mailing')
    search_fields = ('full_name', 'username')
    readonly_fields = ('first_visit', 'last_visit')


@admin.register(Venue)
class VenueAdmin(ModelAdmin):
    list_display = ('name', 'time_open', 'time_close', 'table_count', 'book_len', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Book)
class BookAdmin(ModelAdmin):
    list_display = ('date_book', 'time_book', 'people_count', 'venue', 'user_id', 'status', 'is_active')
    list_filter = ('venue', 'date_book', 'status', 'is_active')
    search_fields = ('comment', )
    readonly_fields = ('created_at', 'updated_at', 'qr_id')


class EventOptionInline(TabularInline):
    model = EventOption
    extra = 0
    fields = ('name', 'all_place', 'empty_place', 'price', 'is_active')
    readonly_fields = ('created_at', 'updated_at')
    show_change_link = True


class TicketInline(TabularInline):
    model = Ticket
    extra = 0
    fields = ('user', 'option', 'status', 'is_active')
    readonly_fields = ('created_at', 'updated_at')
    show_change_link = True


@admin.register(Event)
class EventAdmin(ModelAdmin):
    list_display = ('name', 'date_event', 'time_event', 'venue', 'creator_id', 'is_active')
    list_filter = ('venue', 'date_event', 'is_active')
    search_fields = ('name', 'text')
    readonly_fields = ('created_at', 'updated_at', 'entities', 'photo_id', 'gs_page')
    inlines = [EventOptionInline, TicketInline]


@admin.register(EventOption)
class EventOptionAdmin(ModelAdmin):
    list_display = ('name', 'event', 'all_place', 'empty_place', 'price', 'is_active')
    list_filter = ('event', 'is_active')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Ticket)
class TicketAdmin(ModelAdmin):
    list_display = ('option', 'event', 'user', 'status', 'is_active')
    list_filter = ('event', 'option', 'status', 'is_active')
    search_fields = ('user__full_name', 'user__username', 'qr_id', 'gs_sheet')
    readonly_fields = ('created_at', 'updated_at', 'pay_id', 'gs_sheet', 'gs_page', 'gs_row', 'qr_id')
    autocomplete_fields = ('event', 'user', 'option')


@admin.register(AdminLog)
class AdminLogAdmin(ModelAdmin):
    list_display = ('created_at', 'admin_id', 'user_id', 'action')
    list_filter = ('action',)
    search_fields = ('admin_id', 'user_id')
    ordering = ("-created_at",)
    readonly_fields = ('created_at', 'admin_id', 'user_id', 'action', 'comment')


@admin.register(LogError)
class ErrorJournalAdmin(ModelAdmin):
    list_display = ("id", "created_at", "user_id", "message", "comment")
    search_fields = ("user_id", "message", "traceback")
    list_filter = ("created_at",)
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "user_id", "traceback", "message")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "amount", "payment_time", "invoice_id", "uuid")
    readonly_fields = [field.name for field in Payment._meta.fields]
    search_fields = ("invoice_id", "uuid", "phone", "card_pan", "user__username")
    list_filter = ("ps", "store_id", "created_at")
