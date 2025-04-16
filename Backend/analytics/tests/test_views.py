from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from datetime import timedelta
import json

from analytics.models import (
    PlayerAnalytics,
    TeamAnalytics,
    GamePrediction,
    PlayerPerformancePrediction,
    TeamPerformanceTrend
)
from games.models import Game, Team, Player, PlayerGameStats

User = get_user_model()

class BaseAPITestCase(TestCase):
    """Base class for API test cases with authentication setup"""
    
    def setUp(self):
        # Create users
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )
        
        self.normal_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='userpassword'
        )
        
        self.unauthenticated_client = APIClient()
        
        self.user_client = APIClient()
        self.user_client.force_authenticate(user=self.normal_user)
        
        self.admin_client = APIClient()
        self.admin_client.force_authenticate(user=self.admin_user)
        
        # Create base test data
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
        
        self.player = Player.objects.create(
            name='Test Player',
            team=self.team,
            position='PG',
            jersey_number=23,
            nationality='US',
            active=True
        )
        
        self.game = Game.objects.create(
            home_team=self.team,
            away_team=self.opposing_team,
            date_time=timezone.now() + timedelta(days=1),
            venue='Test Arena',
            status='SCHEDULED'
        )
        
        self.past_game = Game.objects.create(
            home_team=self.team,
            away_team=self.opposing_team,
            date_time=timezone.now() - timedelta(days=1),
            venue='Test Arena',
            status='FINISHED',
            home_score=105,
            away_score=98
        )


class AuthenticationTests(BaseAPITestCase):
    """Test authentication for analytics endpoints"""
    
    def test_list_game_predictions(self):
        """Test retrieving the list of game predictions"""
        url = reverse('game-prediction-list')
        response = self.user_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
    
    def test_retrieve_game_prediction(self):
        """Test retrieving a specific game prediction"""
        url = reverse('game-prediction-detail', kwargs={'pk': self.prediction.pk})
        response = self.user_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['game'], self.game.pk)
        self.assertEqual(response.data['home_team_win_probability'], '65.20')
    
    def test_filter_game_predictions_by_game(self):
        """Test filtering game predictions by game"""
        url = reverse('game-prediction-list')
        response = self.user_client.get(url, {'game': self.game.pk})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
        # All results should be for our game
        for item in response.data:
            self.assertEqual(item['game'], self.game.pk)
    
    def test_list_player_predictions(self):
        """Test retrieving the list of player performance predictions"""
        url = reverse('player-prediction-list')
        response = self.user_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
    
    def test_retrieve_player_prediction(self):
        """Test retrieving a specific player prediction"""
        url = reverse('player-prediction-detail', kwargs={'pk': self.player_prediction.pk})
        response = self.user_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['player'], self.player.pk)
        self.assertEqual(response.data['game'], self.game.pk)
    
    def test_generate_predictions_endpoint_admin_only(self):
        """Test that the generate predictions endpoint is admin-only"""
        # Normal user should not be able to access
        url = reverse('player-prediction-generate')
        response = self.user_client.post(url, {'game': self.game.pk})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Admin user should be able to access
        response = self.admin_client.post(url, {'game': self.game.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class RealTimeAnalyticsViewTests(BaseAPITestCase):
    """Test real-time analytics API endpoints"""
    
    def setUp(self):
        super().setUp()
        # Create a live game for real-time analytics
        self.live_game = Game.objects.create(
            home_team=self.team,
            away_team=self.opposing_team,
            date_time=timezone.now(),
            venue='Test Arena',
            status='LIVE',
            home_score=78,
            away_score=72
        )
        
        # Create player game stats for the live game
        self.live_game_stats = PlayerGameStats.objects.create(
            player=self.player,
            game=self.live_game,
            points=18,
            rebounds=4,
            assists=3,
            steals=1,
            blocks=0,
            turnovers=2,
            minutes_played=24,
            field_goals_made=7,
            field_goals_attempted=14,
            three_pointers_made=1,
            three_pointers_attempted=3,
            free_throws_made=3,
            free_throws_attempted=4
        )
    
    def test_process_realtime_data_endpoint_admin_only(self):
        """Test that processing real-time data requires admin privileges"""
        url = reverse('real-time-process-data')
        game_data = {
            'game_id': self.live_game.pk,
            'home_score': 82,
            'away_score': 76,
            'status': 'LIVE',
            'player_stats': [
                {
                    'player_id': self.player.pk,
                    'points': 20,
                    'rebounds': 5,
                    'assists': 4
                }
            ]
        }
        
        # Normal user should not be able to access
        response = self.user_client.post(url, game_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Admin user should be able to access
        response = self.admin_client.post(url, game_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_live_game_stats_endpoint(self):
        """Test retrieving live game statistics"""
        url = reverse('real-time-live-game-stats', kwargs={'game_id': self.live_game.pk})
        response = self.user_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['game_id'], self.live_game.pk)
        self.assertEqual(response.data['home_score'], 78)
        self.assertEqual(response.data['away_score'], 72)
        self.assertIn('player_stats', response.data)
        self.assertGreater(len(response.data['player_stats']), 0)
    
    def test_live_player_stats_endpoint(self):
        """Test retrieving live player statistics"""
        url = reverse('real-time-player-stats', kwargs={'player_id': self.player.pk})
        response = self.user_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['player_id'], self.player.pk)
        self.assertIn('current_game', response.data)
        self.assertIn('season_averages', response.data)
    
    def test_trending_players_endpoint(self):
        """Test retrieving trending players during games"""
        # Create some analytics data
        PlayerAnalytics.objects.create(
            player=self.player,
            date=timezone.now().date(),
            points_avg=20.5,
            rebounds_avg=5.7,
            assists_avg=4.2,
            efficiency_rating=22.5,
            trend_direction='IMPROVING',
            last_10_games_rating=23.8
        )
        
        url = reverse('real-time-trending-players')
        response = self.user_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
        # Should include trend direction
        for player in response.data:
            self.assertIn('trend_direction', player)
            self.assertIn('current_rating', player)
        # Should be denied with 401 Unauthorized
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_authenticated_access(self):
        """Test that authenticated users can access protected endpoints"""
        # Create some test data first
        PlayerAnalytics.objects.create(
            player=self.player,
            date=timezone.now().date(),
            points_avg=20.5,
            rebounds_avg=5.7,
            assists_avg=4.2,
            efficiency_rating=22.5
        )
        
        # Try to access the endpoint as an authenticated user
        url = reverse('player-analytics-list')
        response = self.user_client.get(url)
        
        # Should be successful with 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Response should contain data
        self.assertGreater(len(response.data), 0)


class PlayerAnalyticsViewTests(BaseAPITestCase):
    """Test player analytics API endpoints"""
    
    def setUp(self):
        super().setUp()
        # Create player analytics data
        self.analytics = PlayerAnalytics.objects.create(
            player=self.player,
            date=timezone.now().date(),
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
        
        # Create player game stats for testing
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
    
    def test_list_player_analytics(self):
        """Test retrieving the list of player analytics"""
        url = reverse('player-analytics-list')
        response = self.user_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
    
    def test_retrieve_player_analytics(self):
        """Test retrieving a specific player's analytics"""
        url = reverse('player-analytics-detail', kwargs={'pk': self.analytics.pk})
        response = self.user_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.analytics.pk)
        self.assertEqual(response.data['player'], self.player.pk)
    
    def test_filter_by_player(self):
        """Test filtering analytics by player"""
        url = reverse('player-analytics-list')
        response = self.user_client.get(url, {'player': self.player.pk})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
        # All results should be for our player
        for item in response.data:
            self.assertEqual(item['player'], self.player.pk)
    
    def test_shooting_stats_endpoint(self):
        """Test the shooting stats custom endpoint"""
        url = reverse('player-analytics-shooting-stats', kwargs={'pk': self.analytics.pk})
        response = self.user_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('field_goal_percentage', response.data)
        self.assertIn('three_point_percentage', response.data)
        self.assertIn('free_throw_percentage', response.data)
        self.assertIn('true_shooting_percentage', response.data)
    
    def test_trend_endpoint(self):
        """Test the trend analysis custom endpoint"""
        url = reverse('player-analytics-trend', kwargs={'pk': self.analytics.pk})
        response = self.user_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('trend_direction', response.data)
        self.assertIn('current_rating', response.data)
        self.assertIn('shooting_trend', response.data)


class TeamAnalyticsViewTests(BaseAPITestCase):
    """Test team analytics API endpoints"""
    
    def setUp(self):
        super().setUp()
        # Create team analytics data
        self.analytics = TeamAnalytics.objects.create(
            team=self.team,
            date=timezone.now().date(),
            wins=42,
            losses=24,
            points_scored_avg=108.5,
            points_allowed_avg=102.3,
            win_percentage=63.6
        )
        
        # Create team performance trend data
        self.trend = TeamPerformanceTrend.objects.create(
            team=self.team,
            period_start=timezone.now().date() - timedelta(days=30),
            period_end=timezone.now().date(),
            period_type='MONTH',
            games_played=15,
            wins=10,
            losses=5,
            points_scored_avg=107.3,
            points_allowed_avg=101.8,
            q1_points_scored_avg=26.8,
            q2_points_scored_avg=27.1,
            q3_points_scored_avg=25.5,
            q4_points_scored_avg=27.9,
            q1_points_allowed_avg=25.2,
            q2_points_allowed_avg=24.9,
            q3_points_allowed_avg=26.3,
            q4_points_allowed_avg=25.4,
            home_wins=6,
            home_losses=2,
            away_wins=4,
            away_losses=3,
            home_points_scored_avg=110.2,
            home_points_allowed_avg=100.3,
            away_points_scored_avg=104.4,
            away_points_allowed_avg=103.3,
            streak_type='WIN',
            streak_count=3,
            trend_direction='IMPROVING',
            offensive_efficiency=110.5,
            defensive_efficiency=105.2,
            pace=98.5
        )
    
    def test_list_team_analytics(self):
        """Test retrieving the list of team analytics"""
        url = reverse('team-analytics-list')
        response = self.user_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
    
    def test_retrieve_team_analytics(self):
        """Test retrieving a specific team's analytics"""
        url = reverse('team-analytics-detail', kwargs={'pk': self.analytics.pk})
        response = self.user_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.analytics.pk)
        self.assertEqual(response.data['team'], self.team.pk)
    
    def test_filter_by_team(self):
        """Test filtering analytics by team"""
        url = reverse('team-analytics-list')
        response = self.user_client.get(url, {'team': self.team.pk})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
        # All results should be for our team
        for item in response.data:
            self.assertEqual(item['team'], self.team.pk)
    
    def test_team_trends_list(self):
        """Test retrieving team performance trends"""
        url = reverse('team-performance-trend-list')
        response = self.user_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
    
    def test_team_trends_filter(self):
        """Test filtering team trends by period type"""
        url = reverse('team-performance-trend-list')
        response = self.user_client.get(url, {'period_type': 'MONTH'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)
        # All results should have the specified period type
        for item in response.data:
            self.assertEqual(item['period_type'], 'MONTH')
    
    def test_quarter_analysis_endpoint(self):
        """Test the quarter-by-quarter analysis endpoint"""
        url = reverse('team-performance-trend-quarter-analysis', kwargs={'pk': self.trend.pk})
        response = self.user_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('quarters', response.data)
        self.assertIn('q1', response.data['quarters'])
        self.assertIn('strongest_quarter', response.data)
        self.assertIn('weakest_quarter', response.data)
        
    def test_home_away_splits_endpoint(self):
        """Test the home/away performance splits endpoint"""
        url = reverse('team-performance-trend-home-away-splits', kwargs={'pk': self.trend.pk})
        response = self.user_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('home', response.data)
        self.assertIn('away', response.data)
        self.assertIn('win_percentage', response.data['home'])
        self.assertIn('point_differential', response.data['away'])


class GamePredictionViewTests(BaseAPITestCase):
    """Test game prediction API endpoints"""
    
    def setUp(self):
        super().setUp()
        # Create game prediction data
        self.prediction = GamePrediction.objects.create(
            game=self.game,
            home_team_win_probability=65.2,
            predicted_home_score=110,
            predicted_away_score=102,
            home_q1_score=27,
            home_q2_score=28,
            home_q3_score=26,
            home_q4_score=29,
            away_q1_score=25,
            away_q2_score=26,
            away_q3_score=27,
            away_q4_score=24,
            key_matchup_factors=json.dumps({
                'key_player_matchups': [],
                'home_advantage': 'strong',
                'predicted_pace': 'moderate'
            })
        )
        
        # Create player prediction
        self.player_prediction = PlayerPerformancePrediction.objects.create(
            player=self.player,
            game=self.game,
            predicted_points=22,
            predicted_rebounds=5,
            predicted_assists=4,
            predicted_steals=1,
            predicted_blocks=0,
            predicted_minutes=32,
            predicted_efficiency=23.5,
            confidence_score=75.0,
            factors=json.dumps({
                'recent_form': 'good',
                'matchup_history': 'favorable',
                'minutes_projection': 'high'
            })
        )
    
    def test_list_game_predictions(self):
        """Test retrieving the list of game predictions"""
        url = reverse('game-prediction-list')
        response = self.user_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

