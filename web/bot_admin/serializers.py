from rest_framework import serializers


class BookSerializer(serializers.Serializer):
    spreadsheetId = serializers.CharField()
    sheetId = serializers.IntegerField()
    sheetName = serializers.CharField()
    rowNumber = serializers.IntegerField(min_value=1)
    bookId = serializers.IntegerField(default=None, required=False)
    name = serializers.CharField()
    time = serializers.CharField()
    person = serializers.IntegerField()
    comment = serializers.CharField(default=None, required=False)
    status = serializers.CharField()


class TicketSerializer(serializers.Serializer):
    spreadsheetId = serializers.CharField()
    sheetId = serializers.IntegerField()
    sheetName = serializers.CharField()
    rowNumber = serializers.IntegerField()
    ticketId = serializers.IntegerField(required=False, default=0)
    option = serializers.CharField()
    status = serializers.CharField()


# payments/serializers.py
class PaymentSerializer(serializers.Serializer):
    store_id = serializers.CharField()
    amount = serializers.IntegerField()
    invoice_id = serializers.CharField()
    billing_id = serializers.CharField(required=False, allow_null=True, allow_blank=True, default=None)
    payment_time = serializers.DateTimeField()
    phone = serializers.CharField()
    card_pan = serializers.CharField()
    card_token = serializers.CharField()
    uuid = serializers.CharField()
    receipt_url = serializers.URLField()
    sign = serializers.CharField()

