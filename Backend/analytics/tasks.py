import logging
from datetime import timedelta, datetime
from django.utils import timezone
from django.db.models import Q, Avg, Count, Sum, F, Min, Max
from celery import shared_task
import traceback
import json

from games.models import Game, Player, Team, PlayerGameStats
from .models import (
    PlayerAnalytics, 
    TeamAnalytics, 
    GamePrediction, 
    PlayerPerformancePrediction,
    TeamPerformanceTrend
)

logger = logging.getLogger(__name__)

# Player Analytics Tasks

@shared_task
def update_player_analytics(player_id=None, days=30):
    """
    Calculate and update player analytics data.
    Can be run for a specific player or all players.
    
    Args:
        player_id: Optional ID of specific player to update
        days: Number of days of data to include in the calculations
    """
    try:
        from games.models import Player
        
        # Determine which players to process
        if player_id:
            players = Player.objects.filter(id=player_id)
        else:
            # Get all active players
            players = Player.objects.filter(active=True)
        
        today = timezone.now().date()
        start_date = today - timedelta(days=days)
        
        player_count = 0
        for player in players:
            try:
                # Get recent games from player
                player_stats = PlayerGameStats.objects.filter(
                    player=player,
                    game__date_time__date__gte=start_date
                )
                
                if not player_stats.exists():
                    continue
                
                # Calculate averages
                averages = player_stats.aggregate(
                    points_avg=Avg('points'),
                    rebounds_avg=Avg('rebounds'),
                    assists_avg=Avg('assists'),
                    steals_avg=Avg('steals'),
                    blocks_avg=Avg('blocks'),
                    turnovers_avg=Avg('turnovers'),
                    minutes_avg=Avg('minutes_played')
                )
                
                # Calculate shooting percentages
                fg_attempted = player_stats.aggregate(total=Sum('field_goals_attempted'))['total'] or 0
                fg_made = player_stats.aggregate(total=Sum('field_goals_made'))['total'] or 0
                
                three_pt_attempted = player_stats.aggregate(total=Sum('three_pointers_attempted'))['total'] or 0
                three_pt_made = player_stats.aggregate(total=Sum('three_pointers_made'))['total'] or 0
                
                ft_attempted = player_stats.aggregate(total=Sum('free_throws_attempted'))['total'] or 0
                ft_made = player_stats.aggregate(total=Sum('free_throws_made'))['total'] or 0
                
                fg_percentage = (fg_made / fg_attempted * 100) if fg_attempted > 0 else 0
                three_pt_percentage = (three_pt_made / three_pt_attempted * 100) if three_pt_attempted > 0 else 0
                ft_percentage = (ft_made / ft_attempted * 100) if ft_attempted > 0 else 0
                
                # Get efficiency rating
                efficiency_rating = 0
                if player_stats.exists():
                    for stat in player_stats:
                        game_efficiency = (
                            stat.points + 
                            stat.rebounds * 1.2 + 
                            stat.assists * 1.5 + 
                            stat.steals * 2 + 
                            stat.blocks * 2 - 
                            stat.turnovers
                        )
                        if stat.minutes_played > 0:
                            game_efficiency = game_efficiency / stat.minutes_played * 10
                        efficiency_rating += game_efficiency
                    
                    efficiency_rating /= player_stats.count()
                
                # Calculate trend data
                recent_games = player_stats.order_by('-game__date_time')[:10]
                if recent_games.exists():
                    last_10_efficiency = sum(
                        (s.points + s.rebounds * 1.2 + s.assists * 1.5 + s.steals * 2 + s.blocks * 2 - s.turnovers) 
                        / s.minutes_played * 10 if s.minutes_played > 0 else 0
                        for s in recent_games
                    ) / recent_games.count()
                else:
                    last_10_efficiency = 0
                
                # Get previous analytics to determine trend
                prev_analytics = PlayerAnalytics.objects.filter(
                    player=player
                ).order_by('-date').first()
                
                if prev_analytics and prev_analytics.date < today:
                    if last_10_efficiency > float(prev_analytics.efficiency_rating) * 1.1:
                        trend = 'IMPROVING'
                    elif last_10_efficiency < float(prev_analytics.efficiency_rating) * 0.9:
                        trend = 'DECLINING'
                    else:
                        trend = 'STABLE'
                else:
                    trend = 'STABLE'
                
                # Create or update analytics entry
                analytics, created = PlayerAnalytics.objects.update_or_create(
                    player=player,
                    date=today,
                    defaults={
                        'points_avg': averages['points_avg'] or 0,
                        'rebounds_avg': averages['rebounds_avg'] or 0,
                        'assists_avg': averages['assists_avg'] or 0,
                        'steals_avg': averages['steals_avg'] or 0,
                        'blocks_avg': averages['blocks_avg'] or 0,
                        'turnovers_avg': averages['turnovers_avg'] or 0,
                        'minutes_avg': averages['minutes_avg'] or 0,
                        'efficiency_rating': efficiency_rating,
                        'field_goal_percentage': fg_percentage,
                        'three_point_percentage': three_pt_percentage,
                        'free_throw_percentage': ft_percentage,
                        'true_shooting_percentage': analytics.calculate_true_shooting() if not created else 0,
                        'last_10_games_rating': last_10_efficiency,
                        'trend_direction': trend
                    }
                )
                
                # Update true shooting if this is a new record
                if created:
                    analytics.true_shooting_percentage = analytics.calculate_true_shooting()
                    analytics.save()
                
                player_count += 1
                
            except Exception as e:
                logger.error(f"Error updating analytics for player {player.id}: {str(e)}")
                logger.error(traceback.format_exc())
        
        return f"Updated analytics for {player_count} players"
    
    except Exception as e:
        logger.error(f"Error in update_player_analytics task: {str(e)}")
        logger.error(traceback.format_exc())
        raise

# Team Analytics Tasks

@shared_task
def update_team_analytics(team_id=None, days=30):
    """
    Calculate and update team analytics data.
    Can be run for a specific team or all teams.
    
    Args:
        team_id: Optional ID of specific team to update
        days: Number of days of data to include in the calculations
    """
    try:
        from games.models import Team
        
        # Determine which teams to process
        if team_id:
            teams = Team.objects.filter(id=team_id)
        else:
            # Get all active teams
            teams = Team.objects.filter(active=True)
        
        today = timezone.now().date()
        start_date = today - timedelta(days=days)
        
        team_count = 0
        for team in teams:
            try:
                # Get recent games from team
                home_games = Game.objects.filter(
                    home_team=team,
                    date_time__date__gte=start_date,
                    status='FINISHED'
                )
                
                away_games = Game.objects.filter(
                    away_team=team,
                    date_time__date__gte=start_date,
                    status='FINISHED'
                )
                
                total_games = home_games.count() + away_games.count()
                
                if total_games == 0:
                    continue
                
                # Calculate wins and losses
                home_wins = home_games.filter(home_score__gt=F('away_score')).count()
                home_losses = home_games.filter(home_score__lt=F('away_score')).count()
                
                away_wins = away_games.filter(away_score__gt=F('home_score')).count()
                away_losses = away_games.filter(away_score__lt=F('home_score')).count()
                
                total_wins = home_wins + away_wins
                total_losses = home_losses + away_losses
                
                # Calculate points scored and allowed
                points_scored = 0
                points_allowed = 0
                
                for game in home_games:
                    points_scored += game.home_score
                    points_allowed += game.away_score
                
                for game in away_games:
                    points_scored += game.away_score
                    points_allowed += game.home_score
                
                points_scored_avg = points_scored / total_games if total_games > 0 else 0
                points_allowed_avg = points_allowed / total_games if total_games > 0 else 0
                
                win_percentage = (total_wins / total_games) * 100 if total_games > 0 else 0
                
                # Create or update analytics entry
                analytics, created = TeamAnalytics.objects.update_or_create(
                    team=team,
                    date=today,
                    defaults={
                        'wins': total_wins,
                        'losses': total_losses,
                        'points_scored_avg': points_scored_avg,
                        'points_allowed_avg': points_allowed_avg,
                        'win_percentage': win_percentage
                    }
                )
                
                team_count += 1
                
            except Exception as e:
                logger.error(f"Error updating analytics for team {team.id}: {str(e)}")
                logger.error(traceback.format_exc())
        
        return f"Updated analytics for {team_count} teams"
    
    except Exception as e:
        logger.error(f"Error in update_team_analytics task: {str(e)}")
        logger.error(traceback.format_exc())
        raise

@shared_task
def update_team_performance_trends(team_id=None):
    """
    Calculate and update team performance trends data.
    Can be run for a specific team or all teams.
    
    Args:
        team_id: Optional ID of specific team to update
    """
    try:
        from games.models import Team
        
        # Determine which teams to process
        if team_id:
            teams = Team.objects.filter(id=team_id)
        else:
            # Get all active teams
            teams = Team.objects.filter(active=True)
        
        today = timezone.now().date()
        
        # Define time periods
        periods = [
            {
                'type': 'WEEK',
                'start': today - timedelta(days=7),
                'end': today
            },
            {
                'type': 'MONTH',
                'start': today - timedelta(days=30),
                'end': today
            },
            {
                'type': 'SEASON',
                'start': datetime(today.year, 10, 1).date() if today.month > 6 else datetime(today.year - 1, 10, 1).date(),
                'end': today
            }
        ]
        
        trend_count = 0
        for team in teams:
            try:
                for period in periods:
                    # Calculate team performance for this period
                    home_games = Game.objects.filter(
                        home_team=team,
                        date_time__date__gte=period['start'],
                        date_time__date__lte=period['end'],
                        status='FINISHED'
                    )
                    
                    away_games = Game.objects.filter(
                        away_team=team,
                        date_time__date__gte=period['start'],
                        date_time__date__lte=period['end'],
                        status='FINISHED'
                    )
                    
                    all_games = list(home_games) + list(away_games)
                    all_games.sort(key=lambda g: g.date_time)
                    
                    if not all_games:
                        continue
                    
                    # Calculate wins and losses
                    home_wins = home_games.filter(home_score__gt=F('away_score')).count()
                    home_losses = home_games.filter(home_score__lt=F('away_score')).count()
                    
                    away_wins = away_games.filter(away_score__gt=F('home_score')).count()
                    away_losses = away_games.filter(away_score__lt=F('home_score')).count()
                    
                    total_wins = home_wins + away_wins
                    total_losses = home_losses + away_losses
                    
                    # Calculate points scored and allowed
                    home_points_scored = sum(game.home_score for game in home_games)
                    home_points_allowed = sum(game.away_score for game in home_games)
                    
                    away_points_scored = sum(game.away_score for game in away_games)
                    away_points_allowed = sum(game.home_score for game in away_games)
                    
                    total_points_scored = home_points_scored + away_points_scored
                    total_points_allowed = home_points_allowed + away_points_allowed
                    
                    # Calculate averages
                    total_games = len(all_games)
                    points_scored_avg = total_points_scored / total_games if total_games > 0 else 0
                    points_allowed_avg = total_points_allowed / total_games if total_games > 0 else 0
                    
                    home_games_count = home_games.count()
                    away_games_count = away_games.count()
                    
                    home_points_scored_avg = home_points_scored / home_games_count if home_games_count > 0 else 0
                    home_points_allowed_avg = home_points_allowed / home_games_count if home_games_count > 0 else 0
                    
                    away_points_scored_avg = away_points_scored / away_games_count if away_games_count > 0 else 0
                    away_points_allowed_avg = away_points_allowed / away_games_count if away_games_count > 0 else 0
                    
                    # TODO: Quarter-by-quarter stats when available
                    # For now, we'll set defaults
                    # For now, we'll set defaults
                    q1_points_scored_avg = points_scored_avg * 0.25
                    q2_points_scored_avg = points_scored_avg * 0.25
                    q3_points_scored_avg = points_scored_avg * 0.25
                    q4_points_scored_avg = points_scored_avg * 0.25
                    
                    q1_points_allowed_avg = points_allowed_avg * 0.25
                    q2_points_allowed_avg = points_allowed_avg * 0.25
                    q3_points_allowed_avg = points_allowed_avg * 0.25
                    q4_points_allowed_avg = points_allowed_avg * 0.25
                    
                    # Calculate efficiency metrics
                    pace = 100.0  # Default pace estimate (possessions per game)
                    offensive_efficiency = (points_scored_avg / pace) * 100 if pace > 0 else 0
                    defensive_efficiency = (points_allowed_avg / pace) * 100 if pace > 0 else 0
                    
                    # Calculate streak
                    streak_type = None
                    streak_count = 0
                    
                    if all_games:
                        # Determine current streak
                        for game in reversed(all_games):
                            is_win = (game.home_team == team and game.home_score > game.away_score) or \
                                    (game.away_team == team and game.away_score > game.home_score)
                            
                            if streak_count == 0:
                                streak_type = 'WIN' if is_win else 'LOSS'
                                streak_count = 1
                            elif (streak_type == 'WIN' and is_win) or (streak_type == 'LOSS' and not is_win):
                                streak_count += 1
                            else:
                                break
                    
                    # Determine trend direction
                    # Compare first half of period to second half
                    if len(all_games) >= 4:
                        mid_point = len(all_games) // 2
                        first_half = all_games[:mid_point]
                        second_half = all_games[mid_point:]
                        
                        first_half_wins = sum(1 for g in first_half if 
                                         (g.home_team == team and g.home_score > g.away_score) or 
                                         (g.away_team == team and g.away_score > g.home_score))
                        
                        second_half_wins = sum(1 for g in second_half if 
                                          (g.home_team == team and g.home_score > g.away_score) or 
                                          (g.away_team == team and g.away_score > g.home_score))
                        
                        first_half_win_pct = first_half_wins / len(first_half) if first_half else 0
                        second_half_win_pct = second_half_wins / len(second_half) if second_half else 0
                        
                        if second_half_win_pct > first_half_win_pct * 1.25:
                            trend_direction = 'IMPROVING'
                        elif second_half_win_pct < first_half_win_pct * 0.75:
                            trend_direction = 'DECLINING'
                        else:
                            trend_direction = 'STABLE'
                    else:
                        trend_direction = 'STABLE'
                    
                    # Create or update trend entry
                    trend, created = TeamPerformanceTrend.objects.update_or_create(
                        team=team,
                        period_start=period['start'],
                        period_end=period['end'],
                        period_type=period['type'],
                        defaults={
                            'games_played': total_games,
                            'wins': total_wins,
                            'losses': total_losses,
                            'points_scored_avg': points_scored_avg,
                            'points_allowed_avg': points_allowed_avg,
                            
                            # Quarter-by-quarter performance
                            'q1_points_scored_avg': q1_points_scored_avg,
                            'q2_points_scored_avg': q2_points_scored_avg,
                            'q3_points_scored_avg': q3_points_scored_avg,
                            'q4_points_scored_avg': q4_points_scored_avg,
                            'q1_points_allowed_avg': q1_points_allowed_avg,
                            'q2_points_allowed_avg': q2_points_allowed_avg,
                            'q3_points_allowed_avg': q3_points_allowed_avg,
                            'q4_points_allowed_avg': q4_points_allowed_avg,
                            
                            # Home/away splits
                            'home_wins': home_wins,
                            'home_losses': home_losses,
                            'away_wins': away_wins,
                            'away_losses': away_losses,
                            'home_points_scored_avg': home_points_scored_avg,
                            'home_points_allowed_avg': home_points_allowed_avg,
                            'away_points_scored_avg': away_points_scored_avg,
                            'away_points_allowed_avg': away_points_allowed_avg,
                            
                            # Team form indicators
                            'streak_type': streak_type,
                            'streak_count': streak_count,
                            'trend_direction': trend_direction,
                            
                            # Team efficiency metrics
                            'offensive_efficiency': offensive_efficiency,
                            'defensive_efficiency': defensive_efficiency,
                            'pace': pace,
                        }
                    )
                    
                    trend_count += 1
                    
            except Exception as e:
                logger.error(f"Error updating performance trends for team {team.id}: {str(e)}")
                logger.error(traceback.format_exc())
        
        return f"Updated performance trends for {trend_count} team periods"
    
    except Exception as e:
        logger.error(f"Error in update_team_performance_trends task: {str(e)}")
        logger.error(traceback.format_exc())
        raise

# Game Prediction Tasks

@shared_task
def generate_game_predictions(game_id=None, days_ahead=7):
    """
    Generate predictions for upcoming games.
    Can be run for a specific game or all upcoming games.
    
    Args:
        game_id: Optional ID of specific game to predict
        days_ahead: Number of days ahead to generate predictions for
    """
    try:
        from games.models import Game
        
        # Determine which games to process
        if game_id:
            games = Game.objects.filter(id=game_id)
        else:
            # Get upcoming games
            end_date = timezone.now() + timedelta(days=days_ahead)
            games = Game.objects.filter(
                date_time__gte=timezone.now(),
                date_time__lte=end_date,
                status='SCHEDULED'
            ).order_by('date_time')
        
        predictions_count = 0
        for game in games:
            try:
                # Check if prediction already exists and is recent
                existing_prediction = GamePrediction.objects.filter(
                    game=game,
                    created_at__gte=timezone.now() - timedelta(hours=6)  # Only regenerate if older than 6 hours
                ).first()
                
                if existing_prediction:
                    # Skip if recent prediction exists
                    continue
                
                # Create new prediction
                prediction = GamePrediction(game=game)
                prediction.calculate_prediction()  # This populates all the fields and saves the prediction
                
                predictions_count += 1
                
            except Exception as e:
                logger.error(f"Error generating prediction for game {game.id}: {str(e)}")
                logger.error(traceback.format_exc())
        
        return f"Generated predictions for {predictions_count} games"
    
    except Exception as e:
        logger.error(f"Error in generate_game_predictions task: {str(e)}")
        logger.error(traceback.format_exc())
        raise

@shared_task
def generate_player_predictions(game_id=None, days_ahead=7):
    """
    Generate player performance predictions for upcoming games.
    
    Args:
        game_id: Optional ID of specific game to generate predictions for
        days_ahead: Number of days ahead to generate predictions for
    """
    try:
        from games.models import Game, Player
        
        # Determine which games to process
        if game_id:
            games = Game.objects.filter(id=game_id)
        else:
            # Get upcoming games
            end_date = timezone.now() + timedelta(days=days_ahead)
            games = Game.objects.filter(
                date_time__gte=timezone.now(),
                date_time__lte=end_date,
                status='SCHEDULED'
            ).order_by('date_time')
        
        predictions_count = 0
        for game in games:
            try:
                # Get players from both teams
                home_team_players = Player.objects.filter(team=game.home_team, active=True)
                away_team_players = Player.objects.filter(team=game.away_team, active=True)
                
                all_players = list(home_team_players) + list(away_team_players)
                
                for player in all_players:
                    # Check if prediction already exists and is recent
                    existing_prediction = PlayerPerformancePrediction.objects.filter(
                        player=player,
                        game=game,
                        created_at__gte=timezone.now() - timedelta(hours=6)  # Only regenerate if older than 6 hours
                    ).first()
                    
                    if existing_prediction:
                        # Skip if recent prediction exists
                        continue
                    
                    # Create new prediction
                    prediction = PlayerPerformancePrediction(player=player, game=game)
                    prediction.save_prediction()  # This calculates and saves all fields
                    
                    predictions_count += 1
                
            except Exception as e:
                logger.error(f"Error generating player predictions for game {game.id}: {str(e)}")
                logger.error(traceback.format_exc())
        
        return f"Generated player predictions for {predictions_count} players"
    
    except Exception as e:
        logger.error(f"Error in generate_player_predictions task: {str(e)}")
        logger.error(traceback.format_exc())
        raise

# Real-time Analytics Tasks

@shared_task
def process_realtime_game_data(game_id, game_data):
    """
    Process real-time game data to update analytics.
    
    Args:
        game_id: ID of the game being updated
        game_data: Dictionary containing real-time game statistics
    """
    try:
        from games.models import Game
        
        game = Game.objects.get(id=game_id)
        
        # Update game scores
        home_score = game_data.get('home_score', 0)
        away_score = game_data.get('away_score', 0)
        
        game.home_score = home_score
        game.away_score = away_score
        game.status = game_data.get('status', game.status)
        game.save()
        
        # Update player stats
        player_stats = game_data.get('player_stats', [])
        for player_stat in player_stats:
            player_id = player_stat.get('player_id')
            try:
                player_game_stat = PlayerGameStats.objects.get(
                    player_id=player_id,
                    game_id=game_id
                )
                
                # Update player game stats
                player_game_stat.points = player_stat.get('points', player_game_stat.points)
                player_game_stat.rebounds = player_stat.get('rebounds', player_game_stat.rebounds)
                player_game_stat.assists = player_stat.get('assists', player_game_stat.assists)
                player_game_stat.steals = player_stat.get('steals', player_game_stat.steals)
                player_game_stat.blocks = player_stat.get('blocks', player_game_stat.blocks)
                player_game_stat.turnovers = player_stat.get('turnovers', player_game_stat.turnovers)
                player_game_stat.minutes_played = player_stat.get('minutes_played', player_game_stat.minutes_played)
                
                # Update shooting stats
                player_game_stat.field_goals_made = player_stat.get('field_goals_made', player_game_stat.field_goals_made)
                player_game_stat.field_goals_attempted = player_stat.get('field_goals_attempted', player_game_stat.field_goals_attempted)
                player_game_stat.three_pointers_made = player_stat.get('three_pointers_made', player_game_stat.three_pointers_made)
                player_game_stat.three_pointers_attempted = player_stat.get('three_pointers_attempted', player_game_stat.three_pointers_attempted)
                player_game_stat.free_throws_made = player_stat.get('free_throws_made', player_game_stat.free_throws_made)
                player_game_stat.free_throws_attempted = player_stat.get('free_throws_attempted', player_game_stat.free_throws_attempted)
                
                # Calculate efficiency
                player_game_stat.efficiency = (
                    player_game_stat.points + 
                    player_game_stat.rebounds * 1.2 + 
                    player_game_stat.assists * 1.5 + 
                    player_game_stat.steals * 2 + 
                    player_game_stat.blocks * 2 - 
                    player_game_stat.turnovers
                )
                
                if player_game_stat.minutes_played > 0:
                    player_game_stat.efficiency = player_game_stat.efficiency / player_game_stat.minutes_played * 10
                
                player_game_stat.save()
                
            except PlayerGameStats.DoesNotExist:
                # Create new player game stat record if it doesn't exist
                try:
                    from games.models import Player
                    player = Player.objects.get(id=player_id)
                    
                    PlayerGameStats.objects.create(
                        player=player,
                        game_id=game_id,
                        points=player_stat.get('points', 0),
                        rebounds=player_stat.get('rebounds', 0),
                        assists=player_stat.get('assists', 0),
                        steals=player_stat.get('steals', 0),
                        blocks=player_stat.get('blocks', 0),
                        turnovers=player_stat.get('turnovers', 0),
                        minutes_played=player_stat.get('minutes_played', 0),
                        field_goals_made=player_stat.get('field_goals_made', 0),
                        field_goals_attempted=player_stat.get('field_goals_attempted', 0),
                        three_pointers_made=player_stat.get('three_pointers_made', 0),
                        three_pointers_attempted=player_stat.get('three_pointers_attempted', 0),
                        free_throws_made=player_stat.get('free_throws_made', 0),
                        free_throws_attempted=player_stat.get('free_throws_attempted', 0)
                    )
                except Player.DoesNotExist:
                    logger.error(f"Player with ID {player_id} not found")
                except Exception as e:
                    logger.error(f"Error creating player game stats: {str(e)}")
                    logger.error(traceback.format_exc())
        
        # If game is finished, update prediction accuracy
        if game.status == 'FINISHED':
            try:
                # Update game prediction accuracy
                prediction = GamePrediction.objects.filter(game=game).order_by('-created_at').first()
                if prediction:
                    prediction.evaluate_accuracy(game.home_score, game.away_score)
                    
                # Check if we should trigger analytics updates
                update_analytics_after_game.apply_async(
                    args=[game_id],
                    countdown=60  # Wait 1 minute before updating analytics
                )
            except Exception as e:
                logger.error(f"Error updating prediction accuracy: {str(e)}")
                logger.error(traceback.format_exc())
                
        return f"Processed real-time data for game {game_id}"
        
    except Game.DoesNotExist:
        logger.error(f"Game with ID {game_id} not found")
        return None
    except Exception as e:
        logger.error(f"Error processing real-time game data: {str(e)}")
        logger.error(traceback.format_exc())
        raise
        
@shared_task
def update_analytics_after_game(game_id):
    """
    Update analytics after a game is completed.
    Triggers updates for teams and players involved in the game.
    
    Args:
        game_id: ID of the completed game
    """
    try:
        from games.models import Game
        game = Game.objects.get(id=game_id)
        
        # Update team analytics
        update_team_analytics.apply_async(args=[game.home_team_id])
        update_team_analytics.apply_async(args=[game.away_team_id])
        
        # Update team performance trends
        update_team_performance_trends.apply_async(args=[game.home_team_id])
        update_team_performance_trends.apply_async(args=[game.away_team_id])
        
        # Update player analytics
        player_ids = PlayerGameStats.objects.filter(game_id=game_id).values_list('player_id', flat=True)
        for player_id in player_ids:
            update_player_analytics.apply_async(args=[player_id])
            
        return f"Triggered analytics updates after game {game_id}"
        
    except Game.DoesNotExist:
        logger.error(f"Game with ID {game_id} not found")
        return None
    except Exception as e:
        logger.error(f"Error updating analytics after game: {str(e)}")
        logger.error(traceback.format_exc())
        raise

# Data Cleanup and Maintenance Tasks

@shared_task
def cleanup_old_predictions(days=30):
    """
    Remove old game and player predictions to keep database size manageable
    
    Args:
        days: Number of days of predictions to keep
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Delete old game predictions
        old_game_predictions = GamePrediction.objects.filter(created_at__lt=cutoff_date)
        count_game = old_game_predictions.count()
        old_game_predictions.delete()
        
        # Delete old player predictions
        old_player_predictions = PlayerPerformancePrediction.objects.filter(created_at__lt=cutoff_date)
        count_player = old_player_predictions.count()
        old_player_predictions.delete()
        
        return f"Deleted {count_game} old game predictions and {count_player} old player predictions"
        
    except Exception as e:
        logger.error(f"Error cleaning up old predictions: {str(e)}")
        logger.error(traceback.format_exc())
        raise
        
@shared_task
def consolidate_analytics_data(days=90):
    """
    Consolidate daily analytics data into weekly summaries for data older than specified days
    
    Args:
        days: Keep daily data for this many days, consolidate older data
    """
    try:
        cutoff_date = timezone.now().date() - timedelta(days=days)
        
        # Consolidate player analytics
        # For players, we'll keep the latest record for each week
        player_analytics = PlayerAnalytics.objects.filter(date__lt=cutoff_date)
        
        # Group by player and week
        player_weeks = {}
        for analytics in player_analytics:
            # Get year and week number
            year, week, _ = analytics.date.isocalendar()
            player_id = analytics.player_id
            key = f"{player_id}-{year}-{week}"
            
            if key not in player_weeks or analytics.date > player_weeks[key].date:
                player_weeks[key] = analytics
                
        # Delete all records except the latest for each week
        analytics_to_keep = [a.id for a in player_weeks.values()]
        PlayerAnalytics.objects.filter(date__lt=cutoff_date).exclude(id__in=analytics_to_keep).delete()
        
        # Consolidate team analytics - similar approach
        team_analytics = TeamAnalytics.objects.filter(date__lt=cutoff_date)
        
        # Group by team and week
        team_weeks = {}
        for analytics in team_analytics:
            # Get year and week number
            year, week, _ = analytics.date.isocalendar()
            team_id = analytics.team_id
            key = f"{team_id}-{year}-{week}"
            
            if key not in team_weeks or analytics.date > team_weeks[key].date:
                team_weeks[key] = analytics
                
        # Delete all records except the latest for each week
        analytics_to_keep = [a.id for a in team_weeks.values()]
        TeamAnalytics.objects.filter(date__lt=cutoff_date).exclude(id__in=analytics_to_keep).delete()
        
        return f"Consolidated analytics data older than {days} days"
        
    except Exception as e:
        logger.error(f"Error consolidating analytics data: {str(e)}")
        logger.error(traceback.format_exc())
        raise

@shared_task
def validate_analytics_integrity():
    """
    Check and fix data integrity issues in analytics data
    """
    try:
        issues_fixed = 0
        
        # Check for player analytics with invalid efficiency ratings
        invalid_player_analytics = PlayerAnalytics.objects.filter(
            Q(efficiency_rating__lt=0) | 
            Q(efficiency_rating__gt=50) |  # Unrealistic value
            Q(field_goal_percentage__lt=0) |
            Q(field_goal_percentage__gt=100)
        )
        
        for analytic in invalid_player_analytics:
            # Trigger a recalculation by calling update_player_analytics
            update_player_analytics.apply_async(args=[analytic.player_id])
            issues_fixed += 1
            
        # Check for team analytics with invalid win percentages
        invalid_team_analytics = TeamAnalytics.objects.filter(
            Q(win_percentage__lt=0) | 
            Q(win_percentage__gt=100)
        )
        
        for analytic in invalid_team_analytics:
            # Trigger a recalculation by calling update_team_analytics
            update_team_analytics.apply_async(args=[analytic.team_id])
            issues_fixed += 1
            
        return f"Fixed {issues_fixed} analytics integrity issues"
        
    except Exception as e:
        logger.error(f"Error validating analytics integrity: {str(e)}")
        logger.error(traceback.format_exc())
        raise

# Task Scheduling Configuration

def setup_periodic_tasks(sender, **kwargs):
    """
    Set up periodic tasks using Celery beat
    """
    from celery.schedules import crontab
    
    # Daily tasks
    sender.add_periodic_task(
        crontab(hour=4, minute=0),  # 4:00 AM every day
        update_player_analytics.s(),
    )
    
    sender.add_periodic_task(
        crontab(hour=4, minute=30),  # 4:30 AM every day
        update_team_analytics.s(),
    )
    
    sender.add_periodic_task(
        crontab(hour=5, minute=0),  # 5:00 AM every day
        update_team_performance_trends.s(),
    )
    
    # Game prediction tasks
    sender.add_periodic_task(
        crontab(hour=6, minute=0),  # 6:00 AM every day
        generate_game_predictions.s(days_ahead=7),
    )
    
    sender.add_periodic_task(
        crontab(hour=7, minute=0),  # 7:00 AM every day
        generate_player_predictions.s(days_ahead=3),
    )
    
    # Maintenance tasks
    sender.add_periodic_task(
        crontab(hour=2, minute=0, day_of_week=1),  # 2:00 AM every Monday
        cleanup_old_predictions.s(days=30),
    )
    
    sender.add_periodic_task(
        crontab(hour=3, minute=0, day_of_week=1),  # 3:00 AM every Monday
        consolidate_analytics_data.s(days=90),
    )
    
    sender.add_periodic_task(
        crontab(hour=1, minute=0, day_of_week='*/2'),  # 1:00 AM every other day
        validate_analytics_integrity.s(),
    )

# Connect the periodic
