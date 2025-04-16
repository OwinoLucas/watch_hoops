from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from unittest.mock import patch, MagicMock
import json

from analytics.tasks import (
    update_player_analytics,
    update_team_analytics,
    update_team_performance_trends,
    generate_game_predictions,
    generate_player_predictions,
    process_realtime_game_data,
    update_analytics_after_game,
    cleanup_old_predictions,
    consolidate_analytics_data,
    validate_analytics_integrity
)
from analytics.models import (
    PlayerAnalytics,
    TeamAnalytics,
    GamePrediction,
    PlayerPerformancePrediction,
    TeamPerformanceTrend
)
from games.models import Game, Team, Player, PlayerGameStats


class BaseTaskTestCase(TestCase):
    """Base class for task test cases with common setup"""
    
    def setUp(self):
        """Set up test data"""
        # Create teams
        self.team = Team.objects.create(
            name='Test Team',
            home_venue='Test Arena',
            founded_year=2000,
            active=True
        )
        
        self.opposing_team = Team.objects.create(
            name='Opposing Team',
            home_venue='Away Arena',
            founded_year=2001,
            active=True
        )
        
        # Create players
        self.player = Player.objects.create(
            name='Test Player',
            team=self.team,
            position='PG',
            jersey_number=23,
            nationality='US',
            active=True
        )
        
        self.opposing_player = Player.objects.create(
            name='Opposing Player',
            team=self.opposing_team,
            position='PG',
            jersey_number=10,
            nationality='ES',
            active=True
        )
        
        # Create games
        self.past_game = Game.objects.create(
            home_team=self.team,
            away_team=self.opposing_team,
            date_time=timezone.now() - timedelta(days=1),
            venue='Test Arena',
            status='FINISHED',
            home_score=105,
            away_score=98
        )
        
        self.upcoming_game = Game.objects.create(
            home_team=self.team,
            away_team=self.opposing_team,
            date_time=timezone.now() + timedelta(days=1),
            venue='Test Arena',
            status='SCHEDULED'
        )
        
        self.live_game = Game.objects.create(
            home_team=self.team,
            away_team=self.opposing_team,
            date_time=timezone.now(),
            venue='Test Arena',
            status='LIVE',
            home_score=75,
            away_score=70
        )
        
        # Create player game stats
        self.game_stats = PlayerGameStats.objects.create(
            player=self.player,
            game=self.past_game,
            points=25,
            rebounds=8,
            assists=6,
            steals=2,
            blocks=1,
            turnovers=3,
            minutes_played=35,
            field_goals_made=9,
            field_goals_attempted=18,
            three_pointers_made=2,
            three_pointers_attempted=5,
            free_throws_made=5,
            free_throws_attempted=6
        )
        
        # Create initial analytics data
        self.player_analytics = PlayerAnalytics.objects.create(
            player=self.player,
            date=timezone.now().date() - timedelta(days=1),
            points_avg=20.5,
            rebounds_avg=5.7,
            assists_avg=4.2,
            efficiency_rating=22.5,
            field_goal_percentage=48.2,
            three_point_percentage=36.5,
            free_throw_percentage=82.0,
            steals_avg=1.2,
            blocks_avg=0.8,
            turnovers_avg=2.3,
            minutes_avg=32.5,
            last_10_games_rating=21.8,
            trend_direction='STABLE'
        )
        
        self.team_analytics = TeamAnalytics.objects.create(
            team=self.team,
            date=timezone.now().date() - timedelta(days=1),
            wins=42,
            losses=24,
            points_scored_avg=108.5,
            points_allowed_avg=102.3,
            win_percentage=63.6
        )


class AnalyticsCalculationTasksTests(BaseTaskTestCase):
    """Test cases for analytics calculation tasks"""
    
    @patch('analytics.tasks.PlayerAnalytics.objects.update_or_create')
    def test_update_player_analytics_task(self, mock_update_or_create):
        """Test the player analytics update task"""
        # Configure the mock
        mock_update_or_create.return_value = (self.player_analytics, True)
        
        # Call the task directly (not through Celery)
        result = update_player_analytics(player_id=self.player.id)
        
        # Check that the task completed successfully
        self.assertIn("Updated analytics for", result)
        
        # Verify that update_or_create was called
        mock_update_or_create.assert_called()
        
        # Call without player_id (should update all active players)
        with patch('games.models.Player.objects.filter') as mock_filter:
            mock_filter.return_value = [self.player]
            result = update_player_analytics()
            self.assertIn("Updated analytics for", result)
            mock_filter.assert_called_with(active=True)
    
    @patch('analytics.tasks.TeamAnalytics.objects.update_or_create')
    def test_update_team_analytics_task(self, mock_update_or_create):
        """Test the team analytics update task"""
        # Configure the mock
        mock_update_or_create.return_value = (self.team_analytics, True)
        
        # Call the task directly (not through Celery)
        result = update_team_analytics(team_id=self.team.id)
        
        # Check that the task completed successfully
        self.assertIn("Updated analytics for", result)
        
        # Verify that update_or_create was called
        mock_update_or_create.assert_called()
        
        # Call without team_id (should update all active teams)
        with patch('games.models.Team.objects.filter') as mock_filter:
            mock_filter.return_value = [self.team]
            result = update_team_analytics()
            self.assertIn("Updated analytics for", result)
            mock_filter.assert_called_with(active=True)
    
    @patch('analytics.tasks.TeamPerformanceTrend.objects.update_or_create')
    def test_update_team_performance_trends_task(self, mock_update_or_create):
        """Test the team performance trends update task"""
        # Configure the mock
        trend = TeamPerformanceTrend(
            team=self.team,
            period_type='WEEK',
            period_start=timezone.now().date() - timedelta(days=7),
            period_end=timezone.now().date()
        )
        mock_update_or_create.return_value = (trend, True)
        
        # Call the task directly (not through Celery)
        result = update_team_performance_trends(team_id=self.team.id)
        
        # Check that the task completed successfully
        self.assertIn("Updated performance trends for", result)
        
        # Verify that update_or_create was called
        mock_update_or_create.assert_called()
        
        # Call without team_id (should update all active teams)
        with patch('games.models.Team.objects.filter') as mock_filter:
            mock_filter.return_value = [self.team]
            result = update_team_performance_trends()
            self.assertIn("Updated performance trends for", result)
            mock_filter.assert_called_with(active=True)


class PredictionTasksTests(BaseTaskTestCase):
    """Test cases for prediction generation tasks"""
    
    @patch('analytics.tasks.GamePrediction')
    def test_generate_game_predictions_task(self, mock_game_prediction):
        """Test the game prediction generation task"""
        # Configure the mock
        mock_instance = MagicMock()
        mock_game_prediction.objects.filter.return_value.first.return_value = None
        mock_game_prediction.return_value = mock_instance
        
        # Call the task directly for a specific game
        result = generate_game_predictions(game_id=self.upcoming_game.id)
        
        # Check that the task completed successfully
        self.assertIn("Generated predictions for", result)
        
        # Verify that GamePrediction was created and methods were called
        mock_game_prediction.assert_called()
        mock_instance.calculate_prediction.assert_called_once()
        
        # Call without game_id (should generate for all upcoming games)
        mock_game_prediction.reset_mock()
        mock_instance.reset_mock()
        
        with patch('games.models.Game.objects.filter') as mock_filter:
            mock_filter.return_value.order_by.return_value = [self.upcoming_game]
            result = generate_game_predictions()
            self.assertIn("Generated predictions for", result)
            mock_instance.calculate_prediction.assert_called_once()
    
    @patch('analytics.tasks.PlayerPerformancePrediction')
    def test_generate_player_predictions_task(self, mock_player_prediction):
        """Test the player prediction generation task"""
        # Configure the mock
        mock_instance = MagicMock()
        mock_player_prediction.objects.filter.return_value.first.return_value = None
        mock_player_prediction.return_value = mock_instance
        
        # Set up patch for player retrieval
        with patch('games.models.Player.objects.filter') as mock_player_filter:
            mock_player_filter.return_value = [self.player]
            
            # Call the task directly for a specific game
            result = generate_player_predictions(game_id=self.upcoming_game.id)
            
            # Check that the task completed successfully
            self.assertIn("Generated player predictions for", result)
            
            # Verify that PlayerPerformancePrediction was created and methods were called
            mock_player_prediction.assert_called()
            mock_instance.save_prediction.assert_called_once()
        
        # Call without game_id (should generate for all upcoming games and players)
        mock_player_prediction.reset_mock()
        mock_instance.reset_mock()
        
        with patch('games.models.Game.objects.filter') as mock_game_filter:
            mock_game_filter.return_value.order_by.return_value = [self.upcoming_game]
            
            with patch('games.models.Player.objects.filter') as mock_player_filter:
                mock_player_filter.return_value = [self.player]
                
                result = generate_player_predictions()
                self.assertIn("Generated player predictions for", result)
                mock_instance.save_prediction.assert_called_once()


class RealTimeProcessingTasksTests(BaseTaskTestCase):
    """Test cases for real-time data processing tasks"""
    
    @patch('analytics.tasks.Game.objects.get')
    @patch('analytics.tasks.PlayerGameStats.objects.get')
    def test_process_realtime_game_data_task(self, mock_stats_get, mock_game_get):
        """Test the real-time game data processing task"""
        # Configure the mocks
        mock_game = MagicMock(spec=Game)
        mock_game.id = self.live_game.id
        mock_game.home_team_id = self.team.id
        mock_game.away_team_id = self.opposing_team.id
        mock_game_get.return_value = mock_game
        
        mock_stats = MagicMock(spec=PlayerGameStats)
        mock_stats_get.return_value = mock_stats
        
        # Create game data
        game_data = {
            'home_score': 80,
            'away_score': 75,
            'status': 'LIVE',
            'player_stats': [
                {
                    'player_id': self.player.id,
                    'points': 20,
                    'rebounds': 5,
                    'assists': 4,
                    'field_goals_made': 8,
                    'field_goals_attempted': 15
                }
            ]
        }
        
        # Call the task directly
        result = process_realtime_game_data(self.live_game.id, game_data)
        
        # Check that the task completed successfully
        self.assertIn(f"Processed real-time data for game {self.live_game.id}", result)
        
        # Verify that game was updated
        self.assertEqual(mock_game.home_score, 80)
        self.assertEqual(mock_game.away_score, 75)
        self.assertEqual(mock_game.status, 'LIVE')
        mock_game.save.assert_called_once()
        
        # Test player stats update
        mock_stats_get.assert_called_with(player_id=self.player.id, game_id=self.live_game.id)
        self.assertEqual(mock_stats.points, 20)
        self.assertEqual(mock_stats.rebounds, 5)
        self.assertEqual(mock_stats.assists, 4)
        mock_stats.save.assert_called_once()
        
        # Test with finished game status
        game_data['status'] = 'FINISHED'
        mock_game.status = 'FINISHED'
        
        with patch('analytics.tasks.GamePrediction.objects.filter') as mock_pred_filter:
            mock_prediction = MagicMock(spec=GamePrediction)
            mock_pred_filter.return_value.order_by.return_value.first.return_value = mock_prediction
            
            with patch('analytics.tasks.update_analytics_after_game.apply_async') as mock_update_task:
                result = process_realtime_game_data(self.live_game.id, game_data)
                self.assertIn(f"Processed real-time data for game {self.live_game.id}", result)
                
                # Verify prediction accuracy was evaluated
                mock_prediction.evaluate_accuracy.assert_called_once_with(80, 75)
                
                # Verify analytics update was scheduled
                mock_update_task.assert_called_once()
    
    @patch('analytics.tasks.Game.objects.get')
    @patch('analytics.tasks.update_team_analytics.apply_async')
    @patch('analytics.tasks.update_team_performance_trends.apply_async')
    @patch('analytics.tasks.update_player_analytics.apply_async')
    def test_update_analytics_after_game_task(self, mock_player_task, mock_trends_task, mock_team_task, mock_game_get):
        """Test the analytics update after game task"""
        # Configure the mocks
        mock_game = MagicMock(spec=Game)
        mock_game.id = self.past_game.id
        mock_game.home_team_id = self.team.id
        mock_game.away_team_id = self.opposing_team.id
        mock_game_get.return_value = mock_game
        
        # Mock player game stats retrieval
        with patch('analytics.tasks.PlayerGameStats.objects.filter') as mock_stats_filter:
            mock_stats_filter.return_value.values_list.return_value = [self.player.id, self.opposing_player.id]
            
            # Call the task directly
            result = update_analytics_after_game(self.past_game.id)
            
            # Check that the task completed successfully
            self.assertIn(f"Triggered analytics updates after game {self.past_game.id}", result)
            
            # Verify that update tasks were scheduled for both teams
            mock_team_task.assert_any_call(args=[self.team.id])
            mock_team_task.assert_any_call(args=[self.opposing_team.id])
            
            # Verify that trend update tasks were scheduled for both teams
            mock_trends_task.assert_any_call(args=[self.team.id])
            mock_trends_task.assert_any_call(args=[self.opposing_team.id])
            
            # Verify that player update tasks were scheduled
            mock_player_task.assert_any_call(args=[self.player.id])
            mock_player_task.assert_any_call(args=[self.opposing_player.id])


class MaintenanceTasksTests(BaseTaskTestCase):
    """Test cases for data maintenance tasks"""
    
    @patch('analytics.tasks.GamePrediction.objects.filter')
    @patch('analytics.tasks.PlayerPerformancePrediction.objects.filter')
    def test_cleanup_old_predictions_task(self, mock_player_pred_filter, mock_game_pred_filter):
        """Test the old predictions cleanup task"""
        # Configure the mocks
        mock_game_pred_queryset = MagicMock()
        mock_game_pred_queryset.count.return_value = 5
        mock_game_pred_filter.return_value = mock_game_pred_queryset
        
        mock_player_pred_queryset = MagicMock()
        mock_player_pred_queryset.count.return_value = 10
        mock_player_pred_filter.return_value = mock_player_pred_queryset
        
        # Call the task directly
        result = cleanup_old_predictions(days=30)
        
        # Check that the task completed successfully
        self.assertIn("Deleted 5 old game predictions and 10 old player predictions", result)
        
        # Verify that filter and delete were called
        mock_game_pred_filter.assert_called_once()
        mock_player_pred_filter.assert_called_once()
        mock_game_pred_queryset.delete.assert_called_once()
        mock_player_pred_queryset.delete.assert_called_once()
    
    @patch('analytics.tasks.PlayerAnalytics.objects.filter')
    @patch('analytics.tasks.TeamAnalytics.objects.filter')
    def test_consolidate_analytics_data_task(self, mock_team_filter, mock_player_filter):
        """Test the analytics data consolidation task"""
        # Configure the mocks for player analytics
        mock_player_analytics = []
        for i in range(10):
            analytics = MagicMock(spec=PlayerAnalytics)
            analytics.id = i
            analytics.player_id = self.player.id
            analytics.date = timezone.now().date() - timedelta(days=100 + i)
            mock_player_analytics.append(analytics)
        
        mock_player_queryset = MagicMock()
        mock_player_queryset.__iter__.return_value = iter(mock_player_analytics)
        mock_player_filter.return_value = mock_player_queryset
        
        # Configure mocks for team analytics
        mock_team_analytics = []
        for i in range(10):
            analytics = MagicMock(spec=TeamAnalytics)
            analytics.id = i + 100
            analytics.team_id = self.team.id
            analytics.date = timezone.now().date() - timedelta(days=100 + i)
            mock_team_analytics.append(analytics)
        
        mock_team_queryset = MagicMock()
        mock_team_queryset.__iter__.return_value = iter(mock_team_analytics)
        mock_team_filter.return_value = mock_team_queryset
        
        # Mock the exclude method for both querysets
        mock_player_filter.return_value.exclude.return_value = mock_player_queryset
        mock_team_filter.return_value.exclude.return_value = mock_team_queryset
        
        # Call the task directly
        result = consolidate_analytics_data(days=90)
        
        # Check that the task completed successfully
        self.assertIn("Consolidated analytics data older than 90 days", result)
        
        # Verify that filter, exclude, and delete were called
        mock_player_filter.assert_called_once()
        mock_team_filter.assert_called_once()
        mock_player_filter.return_value.exclude.assert_called_once()
        mock_team_filter.return_value.exclude.assert_called_once()
        mock_player_queryset.delete.assert_called_once()
        mock_team_queryset.delete.assert_called_once()
    
    @patch('analytics.tasks.PlayerAnalytics.objects.filter')
    @patch('analytics.tasks.TeamAnalytics.objects.filter')
    @patch('analytics.tasks.update_player_analytics.apply_async')
    @patch('analytics.tasks.update_team_analytics.apply_async')
    def test_validate_analytics_integrity_task(self, mock_team_task, mock_player_task, 
                                               mock_team_filter, mock_player_filter):
        """Test the analytics integrity validation task"""
        # Configure the mocks
        mock_invalid_player_analytics = []
        for i in range(3):
            analytics = MagicMock(spec=PlayerAnalytics)
            analytics.player_id = self.player.id + i
            mock_invalid_player_analytics.append(analytics)
        
        mock_player_queryset = MagicMock()
        mock_player_queryset.__iter__.return_value = iter(mock_invalid_player_analytics)
        mock_player_filter.return_value = mock_player_queryset
        
        mock_invalid_team_analytics = []
        for i in range(2):
            analytics = MagicMock(spec=TeamAnalytics)
            analytics.team_id = self.team.id + i
            mock_invalid_team_analytics.append(analytics)
        
        mock_team_queryset = MagicMock()
        mock_team_queryset.__iter__.return_value = iter(mock_invalid_team_analytics)
        mock_team_filter.return_value = mock_team_queryset
        
        # Call the task directly
        result = validate_analytics_integrity()
        
        # Check that the task completed successfully
        self.assertIn("Fixed 5 analytics integrity issues", result)
        
        # Verify that filter was called with the right conditions
        mock_player_filter.assert_called_once()
        mock_team_filter.assert_called_once()
        
        # Verify that update tasks were scheduled for each invalid record
        self.assertEqual(mock_player_task.call_count, 3)
        self.assertEqual(mock_team_task.call_count, 2)


class TaskSchedulingTests(TestCase):
    """Test the task scheduling configuration"""
    
    @patch('analytics.tasks.update_player_analytics')
    @patch('analytics.tasks.update_team_analytics')
    @patch('analytics.tasks.update_team_performance_trends')
    @patch('analytics.tasks.generate_game_predictions')
    @patch('analytics.tasks.generate_player_predictions')
    @patch('analytics.tasks.cleanup_old_predictions')
    @patch('analytics.tasks.consolidate_analytics_data')
    @patch('analytics.tasks.validate_analytics_integrity')
    def test_setup_periodic_tasks(self, mock_validate, mock_consolidate, mock_cleanup,
                                 mock_player_pred, mock_game_pred, mock_trends, 
                                 mock_team, mock_player):
        """Test the setup_periodic_tasks function"""
        from analytics.tasks import setup_periodic_tasks
        
        # Create a mock sender
        mock_sender = MagicMock()
        
        # Call the setup function
        setup_periodic_tasks(mock_sender)
        
        # Verify that add_periodic_task was called for each scheduled task
        self.assertEqual(mock_sender.add_periodic_task.call_count, 8)
