from django.contrib import admin
from django.urls import path, include


from .views import GoogleSheetWebhookView

urlpatterns = [
    path("edit-book/", GoogleSheetWebhookView.as_view(), name="edit-book"),
]
