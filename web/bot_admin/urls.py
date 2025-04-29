from django.contrib import admin
from django.urls import path, include


from .views import BookView, TicketView

urlpatterns = [
    path("edit-book/", BookView.as_view(), name="edit-book"),
    path("edit-ticket/", TicketView.as_view(), name="edit-ticket"),
]
