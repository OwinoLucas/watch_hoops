from django.shortcuts import render
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Game, MatchStats
from .serializers import MatchSerializer, MatchStatsSerializer
from permissions import IsAdminOrReadOnly

class MatchViewSet(viewsets.ModelViewSet):
    """
    Handles CRUD operations for Matches
    GET /api/matches/matches/ - List all matches
    GET /api/matches/matches/{id}/ - Get specific match
    POST /api/matches/matches/ - Create new match
    PUT /api/matches/matches/{id}/ - Update match
    DELETE /api/matches/matches/{id}/ - Delete match
    """
    queryset = Game.objects.all()
    serializer_class = MatchSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['date_time', 'status']

    @action(detail=False, methods=['get'])
    def live(self, request):
        """
        GET /api/matches/matches/live/ - Get all live matches
        """
        live_matches = Game.objects.filter(status='LIVE')
        serializer = self.get_serializer(live_matches, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """
        GET /api/matches/matches/upcoming/ - Get upcoming matches
        """
        upcoming_matches = Game.objects.filter(
            date_time__gte=timezone.now()
        ).order_by('date_time')[:5]
        serializer = self.get_serializer(upcoming_matches, many=True)
        return Response(serializer.data)

class MatchStatsViewSet(viewsets.ModelViewSet):
    """
    Handles CRUD operations for Match Statistics
    GET /api/matches/match-stats/ - List all match statistics
    GET /api/matches/match-stats/{id}/ - Get specific match statistics
    POST /api/matches/match-stats/ - Create new match statistics
    PUT /api/matches/match-stats/{id}/ - Update match statistics
    DELETE /api/matches/match-stats/{id}/ - Delete match statistics
    """
    queryset = MatchStats.objects.all()
    serializer_class = MatchStatsSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['points', 'assists', 'rebounds']
# Create your views here.
