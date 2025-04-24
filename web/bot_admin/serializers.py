from rest_framework import serializers


class BookingDataSerializer(serializers.Serializer):
    name = serializers.CharField()
    time = serializers.CharField()
    person = serializers.CharField()
    comment = serializers.CharField()
    status = serializers.CharField()


class BookingFromSheetSerializer(serializers.Serializer):
    spreadsheet_id = serializers.CharField()
    sheet_id = serializers.IntegerField()
    row_number = serializers.IntegerField(min_value=1)
    data = BookingDataSerializer()
