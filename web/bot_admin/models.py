from django.db import models
import random

from enums import admin_action_choice, book_status_choice


class Venue(models.Model):
    id = models.AutoField(primary_key=True, verbose_name='ID')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')
    name = models.CharField(max_length=255, verbose_name='Название')
    time_open = models.TimeField(verbose_name='Открытие')
    time_close = models.TimeField(default='23:59', verbose_name='Закрытие')
    table_count = models.IntegerField(verbose_name='Количество столов')
    book_len = models.IntegerField(default=180, verbose_name='Длительность брони (мин)')
    book_gs_id = models.CharField(max_length=255, null=True, blank=True, verbose_name='Google Sheets ID (бронь)')
    event_gs_id = models.CharField(max_length=255, null=True, blank=True, verbose_name='Google Sheets ID (ивенты)')
    admin_chat_id = models.BigIntegerField(default=random.randint(10000, 99999), verbose_name='Chat ID администратора')
    is_active = models.BooleanField(null=True, blank=True, verbose_name='Активен')

    class Meta:
        db_table = 'venues'
        managed = False
        verbose_name = 'Заведение'
        verbose_name_plural = 'Заведения'

    def __str__(self):
        return self.name


class User(models.Model):
    class UserStatus(models.TextChoices):
        USER = 'user', 'Пользователь'
        ADMIN = 'admin', 'Администратор'
        STAFF = 'staff', 'Персонал'

    id = models.BigAutoField(primary_key=True, verbose_name='ID')
    first_visit = models.DateTimeField(auto_now_add=True, verbose_name='Первое посещение')
    last_visit = models.DateTimeField(auto_now=True, verbose_name='Последнее посещение')
    full_name = models.CharField(max_length=255, verbose_name='Имя и фамилия')
    username = models.CharField(max_length=150, null=True, blank=True, verbose_name='Юзернейм')
    status = models.CharField(
        max_length=255, choices=UserStatus.choices, default=UserStatus.USER, verbose_name='Статус'
    )
    mailing = models.BooleanField(default=True, verbose_name='Получает рассылку')
    venue = models.ForeignKey(
        Venue,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='users',
        verbose_name='Заведение'
    )

    class Meta:
        db_table = 'users'
        managed = False
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f"{self.full_name} ({self.username or 'no username'})"


class Book(models.Model):
    id = models.AutoField(primary_key=True, verbose_name='ID')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    user_id = models.BigIntegerField(verbose_name='ID пользователя')
    venue = models.ForeignKey(
        'Venue',
        on_delete=models.CASCADE,
        verbose_name='Заведение',
        related_name='bookings'
    )

    time_book = models.TimeField(verbose_name='Время брони')
    date_book = models.DateField(verbose_name='Дата брони')
    people_count = models.IntegerField(verbose_name='Количество гостей')
    comment = models.CharField(max_length=255, verbose_name='Комментарий')
    qr_id = models.CharField(max_length=255, null=True, blank=True, verbose_name='QR ID')
    gs_row = models.IntegerField(default=2, verbose_name='Строка в таблице')
    status = models.CharField(max_length=255, verbose_name='Статус', choices=book_status_choice)
    is_active = models.BooleanField(default=True, verbose_name='Активна')

    class Meta:
        db_table = 'books'
        managed = False
        verbose_name = 'Бронь'
        verbose_name_plural = 'Брони'

    def __str__(self):
        return f"{self.date_book} {self.time_book} | {self.people_count} гостей"


class Event(models.Model):
    id = models.AutoField(primary_key=True, verbose_name='ID')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    creator_id = models.BigIntegerField(verbose_name='ID создателя')
    venue = models.ForeignKey(
        'Venue',
        on_delete=models.CASCADE,
        verbose_name='Заведение',
        related_name='events'
    )

    time_event = models.TimeField(verbose_name='Время события')
    date_event = models.DateField(verbose_name='Дата события')
    name = models.CharField(max_length=255, verbose_name='Название')
    text = models.TextField(null=True, blank=True, verbose_name='Описание')
    entities = models.TextField(null=True, blank=True, verbose_name='Энтити (разметка)')
    photo_id = models.CharField(max_length=255, null=True, blank=True, verbose_name='ID фото')
    gs_page = models.BigIntegerField(null=True, blank=True, verbose_name='Страница Google Sheets')
    is_active = models.BooleanField(default=True, verbose_name='Активно')

    class Meta:
        db_table = 'events'
        managed = False
        verbose_name = 'Мероприятие'
        verbose_name_plural = 'Мероприятия'

    def __str__(self):
        return f"{self.name} ({self.date_event})"


class EventOption(models.Model):
    id = models.AutoField(primary_key=True, verbose_name='ID')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    event = models.ForeignKey(
        'Event',
        on_delete=models.CASCADE,
        verbose_name='Событие',
        related_name='options'
    )

    name = models.CharField(max_length=255, verbose_name='Название категории')
    all_place = models.IntegerField(verbose_name='Всего мест')
    empty_place = models.IntegerField(verbose_name='Свободных мест')
    price = models.IntegerField(default=0, null=True, blank=True, verbose_name='Цена')
    gs_row = models.IntegerField(null=True, blank=True, verbose_name='Строка в таблице')
    is_active = models.BooleanField(default=True, verbose_name='Активна')

    class Meta:
        db_table = 'events_options'
        managed = False
        verbose_name = 'Категория билета'
        verbose_name_plural = 'Категории билетов'

    def __str__(self):
        return f"{self.name} | {self.event.name if self.event else 'Без события'}"


class Ticket(models.Model):
    id = models.AutoField(primary_key=True, verbose_name='ID')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    event = models.ForeignKey(
        'Event',
        on_delete=models.CASCADE,
        verbose_name='Событие',
        related_name='tickets'
    )
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='tickets'
    )
    option = models.ForeignKey(
        'EventOption',
        on_delete=models.CASCADE,
        verbose_name='Категория билета',
        related_name='tickets'
    )
    pay_id = models.IntegerField(null=True, blank=True, verbose_name='ID платежа')

    qr_id = models.CharField(max_length=255, null=True, blank=True, verbose_name='QR ID')
    gs_sheet = models.CharField(max_length=255, null=True, blank=True, verbose_name='ID таблицы')
    gs_page = models.BigIntegerField(null=True, blank=True, verbose_name='Страница')
    gs_row = models.IntegerField(null=True, blank=True, verbose_name='Строка')
    status = models.CharField(max_length=50, verbose_name='Статус')
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    class Meta:
        db_table = 'tickets'
        managed = False
        verbose_name = 'Билет'
        verbose_name_plural = 'Билеты'

    def __str__(self):
        return f"Билет #{self.id} - {self.event.name} ({self.status})"


class AdminLog(models.Model):
    admin_id = models.BigIntegerField(verbose_name='ID администратора')
    user_id = models.BigIntegerField(null=True, blank=True, verbose_name='ID пользователя')
    action = models.CharField(max_length=255, verbose_name='Действие', choices=admin_action_choice)
    comment = models.TextField(null=True, blank=True, verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')

    class Meta:
        db_table = 'logs_admin'
        managed = False
        verbose_name = 'Журнал действия'
        verbose_name_plural = 'Журнал действий'

    def __str__(self):
        return f"{self.created_at} | {self.action} | {self.admin_id}"


class LogError(models.Model):
    id = models.AutoField(primary_key=True, verbose_name="ID")
    created_at = models.DateTimeField( verbose_name="Дата создания")
    user_id = models.BigIntegerField(verbose_name="ID пользователя")
    traceback = models.TextField(verbose_name="Traceback ошибки")
    message = models.TextField(verbose_name="Сообщение об ошибке")
    comment = models.CharField(max_length=255, blank=True, null=True, verbose_name="Комментарий")

    class Meta:
        db_table = "logs_error"
        verbose_name = "Журнал ошибок"
        verbose_name_plural = "Журнал ошибок"
        managed = False

    def __str__(self):
        return f"Ошибка (User: {self.user_id}) (Error: {self.message})"
