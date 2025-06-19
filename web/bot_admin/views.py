from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from asgiref.sync import async_to_sync
from datetime import datetime

import logging
import hashlib
import json

from . import utils as ut
from .serializers import BookSerializer, TicketSerializer, PaymentSerializer
from .models import Book, Venue, Event, EventOption, Ticket, User, Payment
from web.settings import DATE_FORMAT, PAY_SECRET, TIME_SHORT_FORMAT, REDIS_CLIENT, bot, DEBUG, BOT_LINK
from enums import Key, book_status_inverted_dict, BookStatus


if DEBUG:
    logger = logging.getLogger(__name__)
else:
    logger = logging.getLogger('view_logger')


class BookView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            serializer = BookSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            payload = serializer.validated_data

            spreadsheet_id = payload["spreadsheetId"]
            page_id = payload["sheetId"]
            page_name = payload["sheetName"]
            row_number = payload["rowNumber"]
            book_id = payload["bookId"]
            name = payload["name"]
            time_book_str = payload["time"]
            person = payload["person"]
            comment = payload["comment"]
            book_status = book_status_inverted_dict.get(payload['status'])
            date_book = datetime.strptime(page_name, DATE_FORMAT).date()
            is_active = True if book_status == BookStatus.CONFIRMED.value else False

            if not book_status:
                return Response('status error', status=status.HTTP_400_BAD_REQUEST)

            try:
                time_book = datetime.fromisoformat(time_book_str.replace("Z", "+00:00")).time()
            except Exception as e:
                time_book = datetime.strptime(time_book_str, TIME_SHORT_FORMAT).time()

            if comment == '-':
                comment = None

            if book_id:
                book = Book.get_by_id(book_id=book_id)

                if not book:
                    return Response('book not found', status=status.HTTP_400_BAD_REQUEST)

                book.time_book = time_book.replace(second=0, microsecond=0)
                book.people_count = person
                book.comment = comment
                book.status = book_status
                book.is_active = is_active
                book.save()

                return Response({"status": "ok"}, status=status.HTTP_200_OK)

            else:
                venue = Venue.get_by_book_gs_id(spreadsheet_id)
                if not venue:
                    return Response({"error": "venue not found"}, status=status.HTTP_400_BAD_REQUEST)
                book = Book.objects.create(
                    venue=venue,
                    time_book=time_book,
                    date_book=date_book,
                    people_count=person,
                    comment=comment,
                    gs_row=row_number,
                    status=book_status,
                    is_active=is_active
                )

                return Response({"status": "ok", 'bookId': book.id}, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.warning(e, exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TicketView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            serializer = TicketSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            validated = serializer.validated_data

            spreadsheet_id = validated["spreadsheetId"]
            sheet_id = validated["sheetId"]
            sheet_name = validated["sheetName"]
            row_number = validated["rowNumber"]
            ticket_id = validated['ticketId']
            option_name = validated['option']
            ticket_status_name = validated['status']

            ticket_status = book_status_inverted_dict.get(ticket_status_name)
            if not ticket_status:
                return Response('status error', status=status.HTTP_400_BAD_REQUEST)

            if ticket_id:
                ticket = Ticket.get_by_id(ticket_id)
                ticket_status = book_status_inverted_dict.get(ticket_status_name)

                if not ticket:
                    return Response('ticket not found', status=status.HTTP_400_BAD_REQUEST)

                if ticket.status != ticket_status:
                    ticket.status = ticket_status
                    ticket.is_active = True if ticket_status == BookStatus.CONFIRMED.value else False
                    ticket.save()

                    add_place = 1 if ticket_status == BookStatus.CONFIRMED.value else -1
                    ticket.option.empty_place = ticket.option.empty_place + add_place
                    ticket.option.save()

                return Response({"status": "ok"}, status=status.HTTP_200_OK)

            else:
                event = Event.get_by_gs_page(sheet_id)
                if not event:
                    return Response('event not found', status=status.HTTP_400_BAD_REQUEST)

                option = EventOption.get_by_event_name(event_id=event.id, option_name=option_name)
                if not option:
                    return Response('option not found', status=status.HTTP_400_BAD_REQUEST)

                ticket = Ticket.objects.create(
                    event=event,
                    option=option,
                    gs_sheet=spreadsheet_id,
                    gs_page=sheet_id,
                    gs_row=row_number,
                    status=ticket_status,
                    is_active=True if ticket_status == BookStatus.CONFIRMED.value else False
                )

                return Response({"status": "ok", "ticketId": ticket.id}, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.warning(e, exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PaymentView(APIView):
    def post(self, request):
        try:
            serializer = PaymentSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data

            # Проверка подписи
            expected_sign = hashlib.md5(
                f"{data['store_id']}{data['invoice_id']}{data['amount']}{PAY_SECRET}".encode()
            ).hexdigest()

            if expected_sign != data["sign"]:
                logger.warning(f'sign не прошла')
                # return Response(
                #     {"success": False, "message": "Подпись не совпадает"},
                #     status=status.HTTP_400_BAD_REQUEST
                # )

            # Получение данных из Redis
            logger.warning(f'sign прошла')

            redis_key = f"{Key.PAY_DATA.value}-{data['invoice_id']}"
            raw = REDIS_CLIENT.get(redis_key)

            if not raw:
                return Response(
                    {"success": False, "message": "Данные по invoice_id не найдены в Redis"},
                    status=status.HTTP_404_NOT_FOUND
                )

            redis_data: dict = json.loads(raw)

            logger.warning(f'redis_data: {redis_data}')
            user_id = redis_data.get("user_id")
            full_name = redis_data.get("full_name")
            ticket_id_list = redis_data.get("ticket_id_list")

            # Подтверждение билетов (аналог confirm_tickets)

            ticket_id = None
            book_date = None
            book_time = None
            for ticket_id in ticket_id_list:
                ticket = Ticket.get_by_id(ticket_id)
                book_date = ticket.event.date_event
                book_time = ticket.event.time_event

                # обновляем базу
                Ticket.update(
                    ticket_id=ticket_id,
                    # qr_id=qr_photo_id,
                    status=BookStatus.CONFIRMED.value,
                    pay_id=data["uuid"],
                    is_active=True
                )

                # qr_data = f'{Key.QR_TICKET.value}:{user_id}:{ticket_id}'
                qr_data = f'{BOT_LINK}{Key.QR.value}-{Key.QR_TICKET.value}-{user_id}-{ticket_id}'

                text = ut.get_ticket_text(ticket)

                # создаём и отправляет qr
                qr_photo_id = ut.generate_and_sand_qr(
                    chat_id=user_id,
                    qr_data=qr_data,
                    caption=text,
                )

                # обновляем базу добавляем qr
                Ticket.update(ticket_id=ticket_id, qr_id=qr_photo_id,)

                # обновляем таблицу
                ut.update_book_status_gs(
                    spreadsheet_id=ticket.event.venue.event_gs_id,
                    sheet_name=ticket.event.gs_page,
                    status=BookStatus.CONFIRMED.value,
                    row=ticket.gs_row,
                )

                # письмо админам
                bot.send_message(
                    chat_id=ticket.event.venue.admin_chat_id,
                    text=f"<b>Подтверждён билета на {ticket.event.name} пользователь {full_name}</b>",
                )

            # напоминалка
            ut.create_book_notice(
                book_id=ticket_id,
                book_date=book_date,
                book_time=book_time,
            )

            # Сохраняем платёж
            Payment.objects.create(
                user_id=user_id,
                store_id=data.get("store_id"),
                amount=data.get("amount"),
                invoice_id=data.get("invoice_id"),
                invoice_uuid=data.get("uuid"),
                billing_id=data.get("billing_id"),
                payment_time=data.get("payment_time"),
                phone=data.get("phone"),
                card_pan=data.get("card_pan"),
                card_token=data.get("card_token"),
                ps=data.get("ps"),
                uuid=data.get("uuid"),
                receipt_url=data.get("receipt_url"),
            )

            # Можно удалить данные из Redis, если больше не нужны
            REDIS_CLIENT.delete(redis_key)

            return Response({"success": True}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(e, exc_info=True)
            return Response({"success": False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# redis_key = f"{Key.PAY_DATA.value}-{data['invoice_id']}"
#                 redis_data: dict = {
#                     'user_id': 524275902,
#                     'full_name': 'Рус',
#                     'ticket_id_list': [39],
#                     'data': [
#                         {
#                             'vat': 12,
#                             'price': 100000,
#                             'qty': 1,
#                             'name': 'Ticket-39',
#                             'package_code': '39',
#                             'mxik': '10202001002000000',
#                             'total': 100000
#                         }
#                     ]
#                 }