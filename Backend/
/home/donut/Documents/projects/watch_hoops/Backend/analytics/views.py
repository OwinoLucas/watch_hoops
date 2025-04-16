from games.models import Game, MatchStats
from players.models import Player
from teams.models import Team
        stats = MatchStats.objects.filter(
            player_id=player_id,
            match__date_time__gte=start_date
        ).values('match__date_time__date').annotate(
            points_avg=Avg('points'),
            rebounds_avg=Avg('rebounds'),
            assists_avg=Avg('assists')
        ).order_by('match__date_time__date')
            'home_vs_away_differential': {
                'win_percentage': round(home_win_pct - away_win_pct, 2),
                'points_scored': round(float(trend.home_points_scored_avg) - float(trend.away_points_scored_avg), 2),
                'points_allowed': round(float(trend.home_points_allowed_avg) - float(trend.away_points_allowed_avg), 2),
                'point_differential': round(
                    (float(trend.home_points_scored_avg) - float(trend.home_points_allowed_avg)) -
                    (float(trend.away_points_scored_avg) - float(trend.away_points_allowed_avg)), 2
                ),
            }
        }
                 # Game and Player are already imported
             'win_percentage': round(home_win_pct - away_win_pct, 2),
                'points_scored': round(float(trend.home_points_scored_avg) - float(trend.away_points_scored_avg), 2),
                'points_allowed': round(float(trend.home_points_allowed_avg) - float(trend.away_points_allowed_avg), 2),
                'point_differential': round(
                    (float(trend.home_points_scored_avg) - float(trend.home_points_allowed_avg)) -
                    (float(trend.away_points_scored_avg) - float(trend.away_points_allowed_avg)), 2
                ),
            }
        }
        
        return Response(splits_data)
                # Create the prediction
                prediction = PlayerPerformancePrediction(player=player, game=game)
                prediction.save_prediction()  # This calculates and saves all fields
                predictions_created += 1
        
        return Response({
            'predictions_created': predictions_created,
            'games_processed': len(games),
            'players_processed': len(players)
        })
    
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
        })
        # Game and Player are already imported
        
        # Determine which games to process
            'home_vs_away_differential': {
                'win_percentage': round(home_win_pct - away_win_pct, 2),
            'home_vs_away_differential': {
                'win_percentage': round(home_win_pct - away_win_pct, 2),
                'points_scored': round(float(trend.home_points_scored_avg) - float(trend.away_points_scored_avg), 2),
                'points_allowed': round(float(trend.home_points_allowed_avg) - float(trend.away_points_allowed_avg), 2),
        stats = MatchStats.objects.filter(
            player_id=player_id,
            match__date_time__gte=start_date
        ).values('match__date_time__date').annotate(
            points_avg=Avg('points'),
            rebounds_avg=Avg('rebounds'),
            assists_avg=Avg('assi            'home_vs_away_differential': {
                'win_percentage': round(home_win_pct - away_win_pct, 2),
                'points_scored': round(float(trend.home_points_scored_avg) - float(trend.away_points_scored_avg), 2),
                'points_allowed': round(float(trend.home_points_allowed_avg) - float(trend.away_points_allowed_avg), 2),
                'point_differential': round(
        stats = MatchStats.objects.filter(
            player_id=player_id,
            match__date_time__gte=start_date
        ).values('match__date_time__date').annotate(
            points_avg=Avg('points'),
            rebounds_avg=Avg('rebounds'                'win_percentage': round(home_win_pct - away_win_pct, 2),


        ).order_by('match__date_time__date')
        
        return Response(stats)
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


class AnalyticsViewSet(viewsets.ModelViewSet):
    """
    Base ViewSet for analytics with common functionality
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
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
- away_win_pct, 2),
                'points_scored': round(float(trend.home_points_scored_avg) - float(trend.away_points_scored_avg), 2),
                'points_allowed': round(float(trend.home_points_allowed_avg) - float(trend.away_points_allowed_avg), 2),
                'point_differential': round(
                    (float(trend.home_points_scored_avg) - float(trend.home_points_allowed_avg)) -
                    (float(trend.away_points_scored_avg) - float(trend.away_points_allowed_avg)), 2
                ),
            }
        }


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
        
                'win_percentage': round(home_win_pct - away_win_pct, 2),
                'points_scored': round(float(trend.home_points_scored_avg) - float(trend.away_points_scored_avg), 2),
                'points_allowed': round(float(trend.home_points_allowed_avg) - float(trend.away_points_allowed_avg), 2),
                'point_differential': round(
                    (float(trend.home_points_scored_avg) - float(trend.home_points_allowed_avg)) -
                    (float(trend.away_points_scored_avg) - float(trend.away_points_allowed_avg)), 2
                ),
            }
        }
        
        return Response(splits_data)
