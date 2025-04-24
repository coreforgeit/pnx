from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import BookingFromSheetSerializer


class GoogleSheetWebhookView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = BookingFromSheetSerializer(data=request.data)
        if serializer.is_valid():
            payload = serializer.validated_data

            spreadsheet_id = payload["spreadsheet_id"]
            sheet_id = payload["sheet_id"]
            row_number = payload["row_number"]
            data = payload["data"]

            # 🔧 Здесь можно сохранить в БД, залогировать или отправить в бот
            print(f"[Google Sheets] Запись строки {row_number}: {data}")

            return Response({"status": "ok"}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
