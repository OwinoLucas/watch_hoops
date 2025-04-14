from rest_framework import serializers
from .models import League, Team

class LeagueSerializer(serializers.ModelSerializer):
    class Meta:
        model = League
        fields = '__all__'

class TeamSerializer(serializers.ModelSerializer):
    league_name = serializers.CharField(source='league.name', read_only=True)

    class Meta:
        model = Team
        fields = '__all__'