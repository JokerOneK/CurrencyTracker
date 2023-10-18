from rest_framework import serializers

from .models import Assignment, CurrencyData


class AssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        read_only_fields = ("id", "sum")
        fields = ("id", "first_term", "second_term", "sum")


class AddUserCurrencySerializer(serializers.Serializer):
    currency = serializers.IntegerField()
    threshold = serializers.DecimalField(max_digits=8, decimal_places=4)


class CurrencyDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = CurrencyData
        fields = ['currency', 'date', 'price']


class CurrencyHistorySerializer(serializers.Serializer):
    currency_id = serializers.IntegerField()
    threshold = serializers.DecimalField(max_digits=10, decimal_places=2)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
