from rest_framework import serializers


class BookingDataSerializer(serializers.Serializer):
    name = serializers.CharField()
    time = serializers.CharField()
    person = serializers.IntegerField()
    comment = serializers.CharField(default=None, required=False)
    status = serializers.CharField()


class BookingFromSheetSerializer(serializers.Serializer):
    spreadsheet_id = serializers.CharField()
    sheet_id = serializers.IntegerField()
    sheet_name = serializers.CharField()
    row_number = serializers.IntegerField(min_value=1)
    data = BookingDataSerializer()


class NewTableRowSerializer(serializers.Serializer):
    option = serializers.CharField()
    quantity = serializers.IntegerField()
    price = serializers.IntegerField()
    note = serializers.CharField(allow_blank=True)


class NewTableDataSerializer(serializers.Serializer):
    spreadsheet_id = serializers.CharField()
    sheet_id = serializers.IntegerField()
    sheet_name = serializers.CharField()
    row_number = serializers.IntegerField()
    data = NewTableRowSerializer()