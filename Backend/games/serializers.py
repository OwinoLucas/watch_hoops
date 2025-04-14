from rest_framework import serializers
from .models import Game, MatchStats

class MatchStatsSerializer(serializers.ModelSerializer):
    player_name = serializers.CharField(source='player.first_name', read_only=True)

    class Meta:
        model = MatchStats
        fields = '__all__'

class MatchSerializer(serializers.ModelSerializer):
    home_team_name = serializers.CharField(source='home_team.name', read_only=True)
    away_team_name = serializers.CharField(source='away_team.name', read_only=True)
    stats = MatchStatsSerializer(many=True, read_only=True)

    class Meta:
        model = Game
        fields = '__all__'