from django.shortcuts import render
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Player,PlayerTeamHistory
from .serializers import PlayerSerializer, PlayerStatsSerializer
from permissions import IsAdminOrReadOnly

class PlayerViewSet(viewsets.ModelViewSet):
    """
    Handles CRUD operations for Players
    GET /api/players/players/ - List all players
    GET /api/players/players/{id}/ - Get specific player
    POST /api/players/players/ - Create new player
    PUT /api/players/players/{id}/ - Update player
    DELETE /api/players/players/{id}/ - Delete player
    """
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'team__name']
    ordering_fields = ['last_name', 'team__name', 'position']

    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """
        GET /api/players/players/{id}/statistics/ - Get player's statistics
        """
        player = self.get_object()
        stats = player.stats.all()
        serializer = PlayerStatsSerializer(stats, many=True)
        return Response(serializer.data)

# class PlayerStatsViewSet(viewsets.ModelViewSet):
#     """
#     Handles CRUD operations for Player Statistics
#     GET /api/players/stats/ - List all player statistics
#     GET /api/players/stats/{id}/ - Get specific player statistics
#     POST /api/players/stats/ - Create new player statistics
#     PUT /api/players/stats/{id}/ - Update player statistics
#     DELETE /api/players/stats/{id}/ - Delete player statistics
#     """
#     queryset = PlayerStats.objects.all()
#     serializer_class = PlayerStatsSerializer
#     filter_backends = [filters.OrderingFilter]
#     ordering_fields = ['season_year', 'points_per_game', 'assists_per_game', 'rebounds_per_game']
# # Create your views here.
