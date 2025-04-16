from rest_framework import serializers
from .models import (
    PlayerAnalytics, 
    TeamAnalytics, 
    GamePrediction, 
    PlayerPerformancePrediction,
    TeamPerformanceTrend
)
from players.serializers import PlayerSerializer
from teams.serializers import TeamSerializer
from games.serializers import MatchSerializer as GameSerializer

class PlayerAnalyticsSerializer(serializers.ModelSerializer):
    player = PlayerSerializer(read_only=True)
    
    class Meta:
        model = PlayerAnalytics
        fields = '__all__'

class TeamAnalyticsSerializer(serializers.ModelSerializer):
    team = TeamSerializer(read_only=True)
    
    class Meta:
        model = TeamAnalytics
        fields = '__all__'

class GamePredictionSerializer(serializers.ModelSerializer):
    game = GameSerializer(read_only=True)
    
    class Meta:
        model = GamePrediction
        fields = '__all__'

class PlayerPerformancePredictionSerializer(serializers.ModelSerializer):
    player = PlayerSerializer(read_only=True)
    game = GameSerializer(read_only=True)
    
    class Meta:
        model = PlayerPerformancePrediction
        fields = '__all__'

class TeamPerformanceTrendSerializer(serializers.ModelSerializer):
    team = TeamSerializer(read_only=True)
    
    class Meta:
        model = TeamPerformanceTrend
        fields = '__all__'
