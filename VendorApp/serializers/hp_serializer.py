from rest_framework import serializers
from VendorApp.models import HistoricalPerformance


class HistoricalPerformanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistoricalPerformance
        fields = "__all__"
