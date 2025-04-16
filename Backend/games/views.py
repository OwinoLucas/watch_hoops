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

@action(detail=True, methods=['get'])
def statistics_summary(self, request, pk=None):
    """
    Get game statistics summary including team totals,
    quarter scores, and leading player stats
    """
    game = self.get_object()
    
    # Get team totals
    home_stats = PlayerGameStats.objects.filter(
        game=game,
        player__team=game.home_team
    ).aggregate(
        total_points=Sum('points'),
        total_rebounds=Sum('rebounds'),
        total_assists=Sum('assists'),
        total_steals=Sum('steals'),
        total_blocks=Sum('blocks')
    )
    
    away_stats = PlayerGameStats.objects.filter(
        game=game,
        player__team=game.away_team
    ).aggregate(
        total_points=Sum('points'),
        total_rebounds=Sum('rebounds'),
        total_assists=Sum('assists'),
        total_steals=Sum('steals'),
        total_blocks=Sum('blocks')
    )
    
    # Get quarter scores
    quarter_scores = StatEvent.objects.filter(
        game=game,
        stat_type='POINTS'
    ).values('period').annotate(
        home_points=Sum('value', filter=Q(player__team=game.home_team)),
        away_points=Sum('value', filter=Q(player__team=game.away_team))
    ).order_by('period')
    
    # Get leading scorers
    leading_scorers = PlayerGameStats.objects.filter(
        game=game
    ).select_related('player').order_by('-points')[:5]
    
    return Response({
        'home_team': {
            'name': game.home_team.name,
            'stats': home_stats
        },
        'away_team': {
            'name': game.away_team.name,
            'stats': away_stats
        },
        'quarter_scores': quarter_scores,
        'leading_scorers': PlayerGameStatsSerializer(leading_scorers, many=True).data
    })

@action(detail=True, methods=['get'])
def lineup(self, request, pk=None):
    """
    Get current/planned lineup for the game
    """
    game = self.get_object()
    
    home_lineup = Player.objects.filter(
        team=game.home_team,
        is_active=True
    ).select_related('team')
    
    away_lineup = Player.objects.filter(
        team=game.away_team,
        is_active=True
    ).select_related('team')
    
    return Response({
        'home_team': {
            'name': game.home_team.name,
            'lineup': PlayerSerializer(home_lineup, many=True).data
        },
        'away_team': {
            'name': game.away_team.name,
            'lineup': PlayerSerializer(away_lineup, many=True).data
        }
    })

@action(detail=True, methods=['get'])
def play_by_play(self, request, pk=None):
    """
    Get detailed play-by-play events
    """
    game = self.get_object()
    
    # Get all events sorted by timestamp
    events = StatEvent.objects.filter(
        game=game
    ).select_related(
        'player',
        'player__team'
    ).order_by('timestamp')
    
    return Response({
        'events': StatEventSerializer(events, many=True).data
    })

@action(detail=False, methods=['get'])
def standings(self, request):
    """
    Get league standings
    """
    # Get the specified league or default to first available
    league_id = request.query_params.get('league')
    league = get_object_or_404(League, id=league_id) if league_id else League.objects.first()
    
    teams = Team.objects.filter(league=league)
    standings = []
    
    for team in teams:
        home_games = Game.objects.filter(
            home_team=team,
            is_finished=True
        )
        away_games = Game.objects.filter(
            away_team=team,
            is_finished=True
        )
        
        wins = home_games.filter(home_score__gt=F('away_score')).count() + \
               away_games.filter(away_score__gt=F('home_score')).count()
        
        losses = home_games.filter(home_score__lt=F('away_score')).count() + \
                away_games.filter(away_score__lt=F('home_score')).count()
        
        standings.append({
            'team': TeamSerializer(team).data,
            'wins': wins,
            'losses': losses,
            'win_percentage': wins / (wins + losses) if (wins + losses) > 0 else 0
        })
    
    # Sort by win percentage
    standings.sort(key=lambda x: x['win_percentage'], reverse=True)
    
    return Response({
        'league': LeagueSerializer(league).data,
        'standings': standings
    })

@action(detail=False, methods=['get'])
def schedule(self, request):
    """
    Get upcoming games schedule with filters
    """
    # Get filter parameters
    team_id = request.query_params.get('team')
    league_id = request.query_params.get('league')
    date_from = request.query_params.get('date_from')
    date_to = request.query_params.get('date_to')
    
    # Base queryset
    queryset = Game.objects.filter(
        date_time__gte=timezone.now()
    ).select_related(
        'home_team',
        'away_team',
        'league'
    ).order_by('date_time')
    
    # Apply filters
    if team_id:
        queryset = queryset.filter(
            Q(home_team_id=team_id) | Q(away_team_id=team_id)
        )
    
    if league_id:
        queryset = queryset.filter(league_id=league_id)
    
    if date_from:
        queryset = queryset.filter(date_time__date__gte=date_from)
    
    if date_to:
        queryset = queryset.filter(date_time__date__lte=date_to)
    
    # Paginate results
    page = self.paginate_queryset(queryset)
    serializer = GameSerializer(page, many=True)
    
    return self.get_paginated_response(serializer.data)
