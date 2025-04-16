from rest_framework import serializers
from .models import SalesReport, AttendanceReport, RevenueReport
from games.serializers import MatchSerializer as GameSerializer  # Import MatchSerializer as GameSerializer

class SalesReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesReport
        fields = '__all__'

class AttendanceReportSerializer(serializers.ModelSerializer):
    game = GameSerializer(read_only=True)
    
    class Meta:
        model = AttendanceReport
        fields = '__all__'

class RevenueReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = RevenueReport
        fields = '__all__'
