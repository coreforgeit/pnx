from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime

import logging

from .serializers import BookSerializer, TicketSerializer
from .models import Book, Venue, Event, EventOption, Ticket
from web.settings import DATE_FORMAT, DATETIME_FORMAT_ISO, TIME_SHORT_FORMAT
from enums import Key, book_status_inverted_dict, BookStatus


logger = logging.getLogger(__name__)


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

