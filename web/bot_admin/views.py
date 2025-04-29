from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime

import logging

from .serializers import BookingFromSheetSerializer, NewTableDataSerializer
from .models import Book, Venue
from web.settings import DATE_FORMAT, DATETIME_FORMAT_ISO, TIME_SHORT_FORMAT
from enums import Key, book_status_inverted_dict, BookStatus


logger = logging.getLogger(__name__)


class GoogleSheetWebhookView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            serializer = BookingFromSheetSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            payload = serializer.validated_data

            spreadsheet_id = payload["spreadsheet_id"]
            page_id = payload["sheet_id"]
            page_name = payload["sheet_name"]
            row_number = payload["row_number"]
            data = payload["data"]

            date_book = datetime.strptime(page_name, DATE_FORMAT).date()
            # time_book = datetime.strptime(data['time'], DATETIME_FORMAT_ISO).time()
            try:
                time_book = datetime.fromisoformat(data['time'].replace("Z", "+00:00")).time()
            except Exception as e:
                time_book = datetime.strptime(data['time'], TIME_SHORT_FORMAT).time()

            name = data['name']
            person = data['person']
            comment = data['comment'][:255]
            book_status = book_status_inverted_dict.get(data['status'])
            is_active = True if book_status == BookStatus.CONFIRMED.value else False

            book = Book.get_by_date_row(row=row_number, date_book=date_book)
            if book:
                book.time_book = time_book.replace(second=0)
                book.people_count = person
                book.comment = comment
                book.status = book_status
                book.is_active = is_active
                book.save()
            else:
                venue = Venue.get_by_book_gs_id(spreadsheet_id)
                if not venue:
                    return Response({"error": "sheet not found"}, status=status.HTTP_400_BAD_REQUEST)
                Book.objects.create(
                    venue=venue,
                    time_book=time_book,
                    date_book=date_book,
                    people_count=person,
                    comment=comment,
                    gs_row=row_number,
                    status=book_status,
                    is_active=is_active
                )

            return Response({"status": "ok"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.warning(e, exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class NewTableWebhookView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = NewTableDataSerializer(data=request.data)
        if serializer.is_valid():
            validated = serializer.validated_data

            spreadsheet_id = validated["spreadsheet_id"]
            sheet_id = validated["sheet_id"]
            sheet_name = validated["sheet_name"]
            row_number = validated["row_number"]
            data = validated["data"]

            # Здесь можно сохранять в базу, отправлять дальше и т.д.
            print(f"✅ Получены данные с таблицы {sheet_name}, строка {row_number}: {data}")

            return Response({"status": "ok"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)