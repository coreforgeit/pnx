import telebot
from django.conf import settings


bot = telebot.TeleBot(settings.BOT_TOKEN, parse_mode="html")
BOT_LINK = f"https://t.me/{settings.BOT_USERNAME}?start="
