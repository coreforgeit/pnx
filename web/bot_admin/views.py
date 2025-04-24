from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import BookingFromSheetSerializer
from enums import Key


class GoogleSheetWebhookView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = BookingFromSheetSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        payload = serializer.validated_data

        spreadsheet_id = payload["spreadsheet_id"]
        sheet_id = payload["sheet_id"]
        type_book = payload["type"]
        row_number = payload["row_number"]
        data = payload["data"]

        if type_book == Key.QR_BOOK.value:
            pass



        return Response({"status": "ok"}, status=status.HTTP_200_OK)

