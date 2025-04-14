from django.shortcuts import render
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import League, Team
from .serializers import LeagueSerializer, TeamSerializer
from permissions import IsAdminOrReadOnly

class LeagueViewSet(viewsets.ModelViewSet):
    """
    Handles CRUD operations for Leagues
    GET /api/teams/leagues/ - List all leagues
    GET /api/teams/leagues/{id}/ - Get specific league
    POST /api/teams/leagues/ - Create new league
    PUT /api/teams/leagues/{id}/ - Update league
    DELETE /api/teams/leagues/{id}/ - Delete league
    """
    queryset = League.objects.all()
    serializer_class = LeagueSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    @action(detail=True, methods=['get'])
    def teams(self, request, pk=None):
        """
        GET /api/teams/leagues/{id}/teams/ - Get all teams in a specific league
        """
        league = self.get_object()
        teams = league.teams.all()
        serializer = TeamSerializer(teams, many=True)
        return Response(serializer.data)

class TeamViewSet(viewsets.ModelViewSet):
    """
    Handles CRUD operations for Teams
    GET /api/teams/teams/ - List all teams
    GET /api/teams/teams/{id}/ - Get specific team
    POST /api/teams/teams/ - Create new team
    PUT /api/teams/teams/{id}/ - Update team
    DELETE /api/teams/teams/{id}/ - Delete team
    """
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'league__name']

    @action(detail=True, methods=['get'])
    def roster(self, request, pk=None):
        """
        GET /api/teams/teams/{id}/roster/ - Get all players in a team
        """
        team = self.get_object()
        players = team.players.all()
        from players.serializers import PlayerSerializer
        serializer = PlayerSerializer(players, many=True)
        return Response(serializer.data)