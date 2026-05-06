from django.apps import AppConfig


class BotAdminConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bot_admin'

    verbose_name = 'Бот'
    verbose_name_plural = 'Бот'

    def ready(self):
        from .scheduler import start_scheduler

        start_scheduler()
