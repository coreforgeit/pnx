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
