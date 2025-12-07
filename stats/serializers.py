from rest_framework import serializers
from .models import StatsPeriod, KpiDaily

class KpiDailySerializer(serializers.ModelSerializer):
    class Meta:
        model = KpiDaily
        fields = '__all__'
        
class StatsPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatsPeriod
        fields = '__all__'