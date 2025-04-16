from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone
from django.db.models import Q, Avg, Count, F, Sum
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from datetime import timedelta
import json

from .models import (
    PlayerAnalytics, 
    TeamAnalytics, 
    GamePrediction, 
    PlayerPerformancePrediction,
    TeamPerformanceTrend
)
from .serializers import (
    PlayerAnalyticsSerializer, 
    TeamAnalyticsSerializer, 
    GamePredictionSerializer,
    PlayerPerformancePredictionSerializer,
    TeamPerformanceTrendSerializer
)
from games.models import Game, MatchStats
from players.models import Player
from teams.models import Team


class AnalyticsViewSet(viewsets.ModelViewSet):
    """
    Base ViewSet for analytics with common functionality
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]


class PlayerAnalyticsViewSet(AnalyticsViewSet):
    """
    ViewSet for player analytics
    
    Provides performance metrics, trends, and statistical analysis for players.
    """
    queryset = PlayerAnalytics.objects.all()
    serializer_class = PlayerAnalyticsSerializer
    filterset_fields = ['player', 'date']
    search_fields = ['player__name']
    ordering_fields = ['date', 'points_avg', 'rebounds_avg', 'assists_avg', 'efficiency_rating']
    ordering = ['-date']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        player_id = self.request.query_params.get('player', None)
        team_id = self.request.query_params.get('team', None)
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        
        if player_id:
            queryset = queryset.filter(player_id=player_id)
            
        if team_id:
            queryset = queryset.filter(player__team_id=team_id)
            
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
            
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
            
        return queryset
    
    @action(detail=False, methods=['get'])
    def streaks(self, request):
        """
        Identify players on hot or cold streaks
        """
        streak_type = request.query_params.get('type', 'hot')  # hot or cold
        team_id = request.query_params.get('team', None)
        
        # Get latest analytics for each player
        latest_player_analytics = {}
        for analytic in PlayerAnalytics.objects.order_by('player', '-date'):
            if analytic.player_id not in latest_player_analytics:
                latest_player_analytics[analytic.player_id] = analytic
        
        # Filter by team if specified
        if team_id:
            latest_player_analytics = {k: v for k, v in latest_player_analytics.items() 
                                      if v.player.team_id == int(team_id)}
        
        # Filter by streak type
        if streak_type == 'hot':
            streaking_players = [analytic for analytic in latest_player_analytics.values() 
                               if analytic.trend_direction == 'IMPROVING' and float(analytic.last_10_games_rating) > 15]
        else:  # cold
            streaking_players = [analytic for analytic in latest_player_analytics.values() 
                               if analytic.trend_direction == 'DECLINING' and float(analytic.last_10_games_rating) < 10]
        
        serializer = self.get_serializer(streaking_players, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def trend(self, request, pk=None):
        """
        Get detailed trend analysis for a player
        """
        analytics = self.get_object()
        days = int(request.query_params.get('days', 30))
        
        # Calculate trend data
        trend_direction, rating = analytics.calculate_trend(days=days)
        
        # Get previous analytics for comparison
        prev_analytics = PlayerAnalytics.objects.filter(
            player=analytics.player,
            date__lt=analytics.date
        ).order_by('-date').first()
        
        trend_data = {
            'player_id': analytics.player.id,
            'player_name': analytics.player.user.get_full_name(),
            'trend_direction': trend_direction,
            'current_rating': rating,
            'previous_rating': float(prev_analytics.efficiency_rating) if prev_analytics else None,
            'days_analyzed': days,
            'shooting_trend': {
                'current_fg': float(analytics.field_goal_percentage),
                'previous_fg': float(prev_analytics.field_goal_percentage) if prev_analytics else None,
                'current_3pt': float(analytics.three_point_percentage),
                'previous_3pt': float(prev_analytics.three_point_percentage) if prev_analytics else None,
            }
        }
        
        return Response(trend_data)
    
    @action(detail=False, methods=['get'])
    def efficiency_leaders(self, request):
        """
        Get top players by efficiency rating
        """
        count = int(request.query_params.get('count', 10))
        team_id = request.query_params.get('team', None)
        
        # Get latest analytics for each player
        latest_date = PlayerAnalytics.objects.order_by('-date').first().date if PlayerAnalytics.objects.exists() else None
        
        if not latest_date:
            return Response([])
            
        queryset = PlayerAnalytics.objects.filter(date=latest_date)
        
        if team_id:
            queryset = queryset.filter(player__team_id=team_id)
            
        leaders = queryset.order_by('-efficiency_rating')[:count]
        serializer = self.get_serializer(leaders, many=True)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def player_stats_trend(self, request):
        """Get player statistics trend over time"""
        player_id = request.query_params.get('player_id')
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now().date() - timedelta(days=days)
        
        if not player_id:
            return Response(
                {"error": "player_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        stats = MatchStats.objects.filter(
            player_id=player_id,
            match__date_time__gte=start_date
        ).values('match__date_time__date').annotate(
            points_avg=Avg('points'),
            rebounds_avg=Avg('rebounds'),
            assists_avg=Avg('assists')
        ).order_by('match__date_time__date')
        
        return Response(stats)


class TeamAnalyticsViewSet(AnalyticsViewSet):
    """
    ViewSet for team analytics
    
    Provides team performance metrics, comparisons, and trends.
    """
    queryset = TeamAnalytics.objects.all()
    serializer_class = TeamAnalyticsSerializer
    filterset_fields = ['team', 'date']
    search_fields = ['team__name']
    ordering_fields = ['date', 'wins', 'losses', 'points_scored_avg', 'points_allowed_avg', 'win_percentage']
    ordering = ['-date']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        team_id = self.request.query_params.get('team', None)
        league_id = self.request.query_params.get('league', None)
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        
        if team_id:
            queryset = queryset.filter(team_id=team_id)
            
        if league_id:
            queryset = queryset.filter(team__league_id=league_id)
            
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
            
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
            
        return queryset
    
    @action(detail=False, methods=['get'])
    def rankings(self, request):
        """
        Get team rankings based on specified metrics
        """
        metric = request.query_params.get('metric', 'win_percentage')
        league_id = request.query_params.get('league', None)
        count = int(request.query_params.get('count', 10))
        
        # Get latest analytics for each team
        latest_date = TeamAnalytics.objects.order_by('-date').first().date if TeamAnalytics.objects.exists() else None
        
        if not latest_date:
            return Response([])
            
        queryset = TeamAnalytics.objects.filter(date=latest_date)
        
        if league_id:
            queryset = queryset.filter(team__league_id=league_id)
            
        rankings = queryset.order_by(f'-{metric}')[:count]
        serializer = self.get_serializer(rankings, many=True)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def team_stats(self, request):
        """Get team statistics and comparisons"""
        team_id = request.query_params.get('team_id')
        
        if not team_id:
            return Response(
                {"error": "team_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        team_stats = TeamAnalytics.objects.filter(
            team_id=team_id
        ).order_by('-date').first()
        
        if not team_stats:
            return Response(
                {"error": "No statistics available for this team"},
                status=status.HTTP_404_NOT_FOUND
            )
            
        return Response(TeamAnalyticsSerializer(team_stats).data)


class PlayerPredictionViewSet(AnalyticsViewSet):
    """
    ViewSet for player performance predictions
    """
    queryset = PlayerPerformancePrediction.objects.all()
    serializer_class = PlayerPerformancePredictionSerializer
    filterset_fields = ['player', 'game']
    search_fields = ['player__name']
    ordering_fields = ['game__date_time', 'predicted_efficiency', 'confidence_score']
    ordering = ['-game__date_time']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        player_id = self.request.query_params.get('player', None)
        team_id = self.request.query_params.get('team', None)
        game_id = self.request.query_params.get('game', None)
        min_confidence = self.request.query_params.get('min_confidence', None)
        if min_confidence:
            queryset = queryset.filter(confidence_score__gte=float(min_confidence))
            
        return queryset
        
    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def generate(self, request):
        """
        Generate predictions for players in upcoming games
        Admin-only endpoint
        """
        game_id = request.data.get('game', None)
        team_id = request.data.get('team', None)
        player_id = request.data.get('player', None)
        
        # Game and Player are already imported
        
        # Determine which games to process
        if game_id:
            games = Game.objects.filter(id=game_id, date_time__gt=timezone.now())
        else:
            # Get upcoming games
            games = Game.objects.filter(date_time__gt=timezone.now()).order_by('date_time')[:5]
        
        # Determine which players to process
        if player_id:
            players = Player.objects.filter(id=player_id)
        elif team_id:
            players = Player.objects.filter(team_id=team_id)
        else:
            # Process all players in the upcoming games
            team_ids = []
            for game in games:
                team_ids.append(game.home_team_id)
                team_ids.append(game.away_team_id)
            players = Player.objects.filter(team_id__in=team_ids)
        
        # Generate predictions
        predictions_created = 0
        for game in games:
            for player in players:
                # Only predict for players in this game
                if player.team_id != game.home_team_id and player.team_id != game.away_team_id:
                    continue
                    
                # Check if prediction already exists
                if PlayerPerformancePrediction.objects.filter(player=player, game=game).exists():
                    continue
                
                # Create the prediction
                prediction = PlayerPerformancePrediction(player=player, game=game)
                prediction.save_prediction()  # This calculates and saves all fields
                predictions_created += 1
        
        return Response({
            'predictions_created': predictions_created,
            'games_processed': len(games),
            'players_processed': len(players)
        })
        
        stats = PlayerGameStats.objects.filter(
            player_id=player_id,
            game__date_time__gte=start_date
        ).values('game__date_time__date').annotate(
            points_avg=Avg('points'),
            rebounds_avg=Avg('rebounds'),
            assists_avg=Avg('assists')
        ).order_by('game__date_time__date')
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def team_stats(self, request):
        """Get team statistics and comparisons"""
        team_id = request.query_params.get('team_id')
        
        if not team_id:
            return Response(
                {"error": "team_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        team_stats = TeamAnalytics.objects.filter(
            team_id=team_id
        ).order_by('-date').first()
        
        if not team_stats:
            return Response(
                {"error": "No statistics available for this team"},
                status=status.HTTP_404_NOT_FOUND
            )
            
        return Response(TeamAnalyticsSerializer(team_stats).data)
    
    @action(detail=False, methods=['get'])
    def predictions(self, request):
        """Get game predictions based on historical data"""
        game_id = request.query_params.get('game_id')
        
        if not game_id:
            return Response(
                {"error": "game_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        prediction = GamePrediction.objects.filter(
            game_id=game_id
        ).order_by('-created_at').first()
        
        if not prediction:
            return Response(
                {"error": "No prediction available for this game"},
                status=status.HTTP_404_NOT_FOUND
            )
            
        return Response(GamePredictionSerializer(prediction).data)


class TeamPerformanceTrendViewSet(AnalyticsViewSet):
    """
    ViewSet for team performance trends
    
    Provides analysis of team performance over specific time periods,
    including quarter-by-quarter analysis, home/away splits, and streaks.
    """
    queryset = TeamPerformanceTrend.objects.all()
    serializer_class = TeamPerformanceTrendSerializer
    filterset_fields = ['team', 'period_type']
    search_fields = ['team__name']
    ordering_fields = ['period_end', 'wins', 'losses', 'points_scored_avg', 'offensive_efficiency']
    ordering = ['-period_end']
    
    def get_queryset(self):
        queryset = super().queryset
        team_id = self.request.query_params.get('team', None)
        league_id = self.request.query_params.get('league', None)
        period_type = self.request.query_params.get('period_type', None)
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        streak = self.request.query_params.get('streak', None)
        
        if team_id:
            queryset = queryset.filter(team_id=team_id)
            
        if league_id:
            queryset = queryset.filter(team__league_id=league_id)
            
        if period_type:
            queryset = queryset.filter(period_type=period_type)
            
        if date_from:
            queryset = queryset.filter(period_end__gte=date_from)
            
        if date_to:
            queryset = queryset.filter(period_start__lte=date_to)
            
        if streak:
            queryset = queryset.filter(streak_type=streak)
            
        return queryset
    
    @action(detail=False, methods=['get'])
    def weekly(self, request):
        """
        Get weekly team performance trends
        """
        team_id = request.query_params.get('team', None)
        count = int(request.query_params.get('count', 10))
        
        if not team_id:
            return Response(
                {"error": "team parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        queryset = self.get_queryset().filter(
            team_id=team_id,
            period_type='WEEK'
        ).order_by('-period_end')[:count]
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def monthly(self, request):
        """
        Get monthly team performance trends
        """
        team_id = request.query_params.get('team', None)
        count = int(request.query_params.get('count', 6))
        
        if not team_id:
            return Response(
                {"error": "team parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        queryset = self.get_queryset().filter(
            team_id=team_id,
            period_type='MONTH'
        ).order_by('-period_end')[:count]
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def seasonal(self, request):
        """
        Get seasonal team performance trends
        """
        team_id = request.query_params.get('team', None)
        
        if not team_id:
            return Response(
                {"error": "team parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        queryset = self.get_queryset().filter(
            team_id=team_id,
            period_type='SEASON'
        ).order_by('-period_end')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def quarter_analysis(self, request, pk=None):
        """
        Get quarter-by-quarter performance analysis
        """
        trend = self.get_object()
        
        quarter_data = {
            'team_id': trend.team.id,
            'team_name': trend.team.name,
            'period': f"{trend.period_start} to {trend.period_end}",
            'quarters': {
                'q1': {
                    'points_scored': float(trend.q1_points_scored_avg),
                    'points_allowed': float(trend.q1_points_allowed_avg),
                    'net_rating': float(trend.q1_points_scored_avg) - float(trend.q1_points_allowed_avg),
                },
                'q2': {
                    'points_scored': float(trend.q2_points_scored_avg),
                    'points_allowed': float(trend.q2_points_allowed_avg),
                    'net_rating': float(trend.q2_points_scored_avg) - float(trend.q2_points_allowed_avg),
                },
                'q3': {
                    'points_scored': float(trend.q3_points_scored_avg),
                    'points_allowed': float(trend.q3_points_allowed_avg),
                    'net_rating': float(trend.q3_points_scored_avg) - float(trend.q3_points_allowed_avg),
                },
                'q4': {
                    'points_scored': float(trend.q4_points_scored_avg),
                    'points_allowed': float(trend.q4_points_allowed_avg),
                    'net_rating': float(trend.q4_points_scored_avg) - float(trend.q4_points_allowed_avg),
                },
            },
            'strongest_quarter': self._determine_strongest_quarter(trend),
            'weakest_quarter': self._determine_weakest_quarter(trend),
        }
        
        return Response(quarter_data)
    
    def _determine_strongest_quarter(self, trend):
        """Helper method to determine team's strongest quarter"""
        net_ratings = [
            ('q1', float(trend.q1_points_scored_avg) - float(trend.q1_points_allowed_avg)),
            ('q2', float(trend.q2_points_scored_avg) - float(trend.q2_points_allowed_avg)),
            ('q3', float(trend.q3_points_scored_avg) - float(trend.q3_points_allowed_avg)),
            ('q4', float(trend.q4_points_scored_avg) - float(trend.q4_points_allowed_avg)),
        ]
        
        return max(net_ratings, key=lambda x: x[1])[0]
    
    def _determine_weakest_quarter(self, trend):
        """Helper method to determine team's weakest quarter"""
        net_ratings = [
            ('q1', float(trend.q1_points_scored_avg) - float(trend.q1_points_allowed_avg)),
            ('q2', float(trend.q2_points_scored_avg) - float(trend.q2_points_allowed_avg)),
            ('q3', float(trend.q3_points_scored_avg) - float(trend.q3_points_allowed_avg)),
            ('q4', float(trend.q4_points_scored_avg) - float(trend.q4_points_allowed_avg)),
        ]
        
        return min(net_ratings, key=lambda x: x[1])[0]
    
    @action(detail=True, methods=['get'])
    def home_away_splits(self, request, pk=None):
        """
        Get home/away performance splits for a team within a specific time period.
        
        This endpoint provides detailed comparison of a team's performance at home versus away games,
        including:
        - Win-loss records in each context
        - Scoring averages
        - Point differentials
        - Overall home vs away advantages/disadvantages
        
        Returns a comprehensive analysis object that can be used to determine if a team
        performs significantly better at home or on the road.
        """
        try:
            trend = self.get_object()
            
            # Calculate win percentages with error handling
            home_games_played = trend.home_wins + trend.home_losses
            away_games_played = trend.away_wins + trend.away_losses
            
            # Check if there are enough games for meaningful analysis
            if home_games_played < 2 or away_games_played < 2:
                return Response(
                    {"error": "Insufficient games for meaningful home/away analysis",
                     "home_games": home_games_played,
                     "away_games": away_games_played},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            home_win_pct = (trend.home_wins / home_games_played) * 100 if home_games_played > 0 else 0
            away_win_pct = (trend.away_wins / away_games_played) * 100 if away_games_played > 0 else 0
            
            # Calculate point differentials
            home_point_differential = float(trend.home_points_scored_avg) - float(trend.home_points_allowed_avg)
            away_point_differential = float(trend.away_points_scored_avg) - float(trend.away_points_allowed_avg)
            
            # Format the response with all calculations properly rounded
            splits_data = {
                'team_id': trend.team.id,
                'team_name': trend.team.name,
                'period': f"{trend.period_start} to {trend.period_end}",
                'home': {
                    'games': home_games_played,
                    'wins': trend.home_wins,
                    'losses': trend.home_losses,
                    'win_percentage': round(home_win_pct, 2),
                    'points_scored_avg': round(float(trend.home_points_scored_avg), 2),
                    'points_allowed_avg': round(float(trend.home_points_allowed_avg), 2),
                    'point_differential': round(home_point_differential, 2),
                },
                'away': {
                    'games': away_games_played,
                    'wins': trend.away_wins,
                    'losses': trend.away_losses,
                    'win_percentage': round(away_win_pct, 2),
                    'points_scored_avg': round(float(trend.away_points_scored_avg), 2),
                    'points_allowed_avg': round(float(trend.away_points_allowed_avg), 2),
                    'point_differential': round(away_point_differential, 2),
                },
                'home_vs_away_differential': {
                    'win_percentage': round(home_win_pct - away_win_pct, 2),
                    'points_scored': round(float(trend.home_points_scored_avg) - float(trend.away_points_scored_avg), 2),
                    'points_allowed': round(float(trend.home_points_allowed_avg) - float(trend.away_points_allowed_avg), 2),
                    'point_differential': round(home_point_differential - away_point_differential, 2),
                    'advantage': 'home' if home_point_differential > away_point_differential else 'away',
                    'advantage_strength': 'strong' if abs(home_point_differential - away_point_differential) > 10 else 
                                         'moderate' if abs(home_point_differential - away_point_differential) > 5 else 'slight'
                }
            }
            
            return Response(splits_data)
            
        except TeamPerformanceTrend.DoesNotExist:
            return Response(
                {"error": "Team performance trend not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"Error calculating home/away splits: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
