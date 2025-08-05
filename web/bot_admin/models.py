from django.db import models
from django.contrib.postgres.fields import ArrayField
from datetime import date
import typing as t
import random


from enums import admin_action_choice, book_status_choice, UserStatus, user_status_choice


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

    objects: models.Manager = models.Manager()

    class Meta:
        db_table = 'venues'
        managed = False
        verbose_name = 'Заведение'
        verbose_name_plural = 'Заведения'

    def __str__(self):
        return self.name

    @classmethod
    def get_by_book_gs_id(cls, book_gs_id: str) -> t.Optional[t.Self]:
        return cls.objects.filter(book_gs_id=book_gs_id).first()


class User(models.Model):
    id = models.BigAutoField(primary_key=True, verbose_name='ID')
    first_visit = models.DateTimeField(auto_now_add=True, verbose_name='Первое посещение')
    last_visit = models.DateTimeField(auto_now=True, verbose_name='Последнее посещение')
    full_name = models.CharField(max_length=255, verbose_name='Имя и фамилия')
    username = models.CharField(max_length=150, null=True, blank=True, verbose_name='Юзернейм')
    status = models.CharField(
        max_length=255, choices=user_status_choice, default=UserStatus.USER.value, verbose_name='Статус'
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

    objects: models.Manager = models.Manager()

    def __str__(self):
        return f"{self.full_name} ({self.username or 'no username'})"

    @classmethod
    def get_by_id(cls, user_id: str) -> t.Optional[t.Self]:
        return cls.objects.filter(id=user_id).first()


class Book(models.Model):
    id = models.AutoField(primary_key=True, verbose_name='ID')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    # user_id = models.BigIntegerField(verbose_name='ID пользователя', null=True)
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='books',
        null=True
    )
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

    objects: models.Manager = models.Manager()

    class Meta:
        db_table = 'books'
        managed = False
        verbose_name = 'Бронь'
        verbose_name_plural = 'Брони'

    def __str__(self):
        return f"{self.date_book} {self.time_book} | {self.people_count} гостей"

    @classmethod
    def get_by_id(cls, book_id: int) -> t.Optional[t.Self]:
        return cls.objects.filter(id=book_id).first()


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

    close_msg = models.TextField(null=True, blank=True, verbose_name='Закрывающее сообщение')
    close_msg_entities = models.TextField(null=True, blank=True, verbose_name='Закрывающее сообщение (разметка)')

    objects: models.Manager = models.Manager()

    class Meta:
        db_table = 'events'
        managed = False
        verbose_name = 'Мероприятие'
        verbose_name_plural = 'Мероприятия'

    def __str__(self):
        return f"{self.name} ({self.date_event})"

    @classmethod
    def get_by_gs_page(cls, gs_page: int) -> t.Optional[t.Self]:
        return cls.objects.filter(gs_page=gs_page).first()

    @classmethod
    def get_by_id(cls, event_id: int) -> t.Optional[t.Self]:
        return cls.objects.filter(id=event_id).first()


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

    objects: models.Manager = models.Manager()

    class Meta:
        db_table = 'events_options'
        managed = False
        verbose_name = 'Категория билета'
        verbose_name_plural = 'Категории билетов'

    def __str__(self):
        return f"{self.name} | {self.event.name if self.event else 'Без события'}"

    @classmethod
    def get_by_event_name(cls, event_id: int, option_name: str) -> t.Optional[t.Self]:
        return cls.objects.filter(event_id=event_id, name=option_name).first()


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
        related_name='tickets',
        null=True
    )
    option = models.ForeignKey(
        'EventOption',
        on_delete=models.CASCADE,
        verbose_name='Категория билета',
        related_name='tickets'
    )
    # pay_id = models.IntegerField(null=True, blank=True, verbose_name='ID платежа')
    pay_id = models.CharField(null=True, blank=True, verbose_name='ID платежа')

    qr_id = models.CharField(max_length=255, null=True, blank=True, verbose_name='QR ID')
    gs_sheet = models.CharField(max_length=255, null=True, blank=True, verbose_name='ID таблицы')
    gs_page = models.BigIntegerField(null=True, blank=True, verbose_name='Страница')
    gs_row = models.IntegerField(null=True, blank=True, verbose_name='Строка')
    status = models.CharField(max_length=50, verbose_name='Статус')
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    objects: models.Manager = models.Manager()

    class Meta:
        db_table = 'tickets'
        managed = False
        verbose_name = 'Билет'
        verbose_name_plural = 'Билеты'

    def __str__(self):
        return f"Билет #{self.id} - {self.event.name} ({self.status})"

    @classmethod
    def get_by_id(cls, ticket_id: int) -> t.Optional[t.Self]:
        return cls.objects.select_related('event__venue', 'option').filter(id=ticket_id).first()

    @classmethod
    def update(
            cls,
            ticket_id: int,
            qr_id: str = None,
            status: str = None,
            pay_id: str = None,
            is_active: bool = True
    ) -> None:
        ticket = cls.objects.filter(id=ticket_id).first()
        if not ticket:
            return

        if qr_id:
            ticket.qr_id = qr_id
        if status:
            ticket.status = status
        if pay_id:
            ticket.pay_id = pay_id
        if is_active is not None:
            ticket.is_active = is_active
        ticket.save()


class Payment(models.Model):
    id = models.BigAutoField(primary_key=True, verbose_name='ID')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')

    user = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
        verbose_name='Пользователь'
    )

    store_id = models.CharField(max_length=50, verbose_name='ID магазина')
    amount = models.PositiveBigIntegerField(verbose_name='Сумма')
    invoice_id = models.CharField(max_length=255, verbose_name='ID счёта')
    invoice_uuid = models.CharField(max_length=255, verbose_name='UUID счёта')
    billing_id = models.CharField(
        max_length=255, null=True, blank=True, verbose_name='ID плательщика'
    )
    payment_time = models.DateTimeField(verbose_name='Время оплаты')
    phone = models.CharField(max_length=20, verbose_name='Телефон', null=True, blank=True)
    card_pan = models.CharField(max_length=20, verbose_name='Маска карты', null=True, blank=True)
    card_token = models.CharField(max_length=255, verbose_name='Токен карты', null=True, blank=True)
    ps = models.CharField(max_length=50, verbose_name='Платёжная система', null=True, blank=True)
    uuid = models.CharField(max_length=255, verbose_name='UUID транзакции', null=True, blank=True)
    receipt_url = models.URLField(verbose_name='Ссылка на чек', null=True, blank=True)
    tickets = ArrayField(
        base_field=models.IntegerField(),
        default=list,
        blank=True,
        verbose_name='ID билетов'
    )

    objects: models.Manager = models.Manager()

    class Meta:
        db_table = 'payments'
        verbose_name = "Платёж"
        verbose_name_plural = "Платежи"
        ordering = ["-created_at"]
        managed = False

    def __str__(self):
        return f"Payment #{self.id} — {self.amount} сум"


class AdminLog(models.Model):
    # admin_id = models.BigIntegerField(verbose_name='ID администратора')
    # user_id = models.BigIntegerField(null=True, blank=True, verbose_name='ID пользователя')
    admin = models.ForeignKey('User', on_delete=models.CASCADE, verbose_name='Админ', related_name='logs_admin')
    user = models.ForeignKey(
        'User', on_delete=models.CASCADE, verbose_name='Пользователь', null=True, blank=True, related_name='logs_user'
    )
    action = models.CharField(max_length=255, verbose_name='Действие', choices=admin_action_choice)
    comment = models.TextField(null=True, blank=True, verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')

    objects: models.Manager = models.Manager()

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
    # user_id = models.BigIntegerField(verbose_name="ID пользователя")
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='log_errors',
        null=True
    )
    traceback = models.TextField(verbose_name="Traceback ошибки")
    message = models.TextField(verbose_name="Сообщение об ошибке")
    comment = models.CharField(max_length=255, blank=True, null=True, verbose_name="Комментарий")

    objects: models.Manager = models.Manager()

    class Meta:
        db_table = "logs_error"
        verbose_name = "Журнал ошибок"
        verbose_name_plural = "Журнал ошибок"
        managed = False

    def __str__(self):
        return f"Ошибка (User: {self.user_id}) (Error: {self.message})"
