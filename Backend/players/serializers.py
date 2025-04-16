from rest_framework import serializers
from .models import Player, PlayerTeamHistory

class PlayerStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerTeamHistory
        fields = '__all__'

class PlayerSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source='team.name', read_only=True)
    stats = PlayerStatsSerializer(many=True, read_only=True)

    class Meta:
        model = Player
        fields = '__all__'