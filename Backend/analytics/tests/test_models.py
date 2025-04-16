from django.test import TestCase
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta, datetime
from decimal import Decimal
import json

from analytics.models import (
    PlayerAnalytics,
    TeamAnalytics,
    GamePrediction,
    PlayerPerformancePrediction,
    TeamPerformanceTrend
)
from games.models import Game, Team, Player, PlayerGameStats


class PlayerAnalyticsModelTests(TestCase):
    """Test cases for PlayerAnalytics model methods and calculations"""
    
    def setUp(self):
        """Set up test data"""
        # Create a team
        self.team = Team.objects.create(
            name='Test Team',
            home_venue='Test Arena',
            founded_year=2000
        )
        
        # Create a player
        self.player = Player.objects.create(
            name='Test Player',
            team=self.team,
            position='PG',
            jersey_number=23,
            nationality='US',
            date_of_birth='1990-01-01'
        )
        
        # Create player analytics
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
        
        # Create some game stats for testing
        game_date = timezone.now() - timedelta(days=1)
        self.game = Game.objects.create(
            home_team=self.team,
            away_team=Team.objects.create(name='Opponent', home_venue='Away Arena', founded_year=2001),
            date_time=game_date,
            venue='Test Arena',
            status='FINISHED',
            home_score=105,
            away_score=98
        )
        
        # Create player game stats
        self.game_stats = PlayerGameStats.objects.create(
            player=self.player,
            game=self.game,
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
    
    def test_calculate_true_shooting(self):
        """Test the true shooting percentage calculation"""
        ts_pct = self.analytics.calculate_true_shooting()
        self.assertIsInstance(ts_pct, float)
        self.assertTrue(0 <= ts_pct <= 100)
        
        # With the sample stats we set up (25 points, 18 FGA, 6 FTA)
        # TS% = 25 / (2 * (18 + (0.44 * 6))) = 25 / (2 * 20.64) = 25 / 41.28 ≈ 0.6057 * 100 = 60.57%
        expected_ts = 25.0 / (2 * (18 + (0.44 * 6))) * 100
        self.assertAlmostEqual(ts_pct, expected_ts, places=2)
    
    def test_calculate_trend(self):
        """Test the player trend calculation"""
        # Create games for two different time periods
        today = timezone.now().date()
        
        # Create more recent games (improving performance)
        for i in range(3):
            game = Game.objects.create(
                home_team=self.team,
                away_team=Team.objects.create(name=f'Opponent {i}', home_venue='Away Arena', founded_year=2001),
                date_time=timezone.now() - timedelta(days=i+1),
                venue='Test Arena',
                status='FINISHED',
                home_score=105 + i,
                away_score=98 - i
            )
            
            # Create player game stats with higher efficiency in recent games
            PlayerGameStats.objects.create(
                player=self.player,
                game=game,
                points=28 + i,
                rebounds=9,
                assists=7,
                steals=2,
                blocks=1,
                turnovers=2,
                minutes_played=35,
                field_goals_made=10,
                field_goals_attempted=18,
                three_pointers_made=3,
                three_pointers_attempted=6,
                free_throws_made=5,
                free_throws_attempted=6,
                efficiency=25.0 + i
            )
        
        # Create older games (lower performance)
        for i in range(3):
            game = Game.objects.create(
                home_team=self.team,
                away_team=Team.objects.create(name=f'Opponent {i+3}', home_venue='Away Arena', founded_year=2001),
                date_time=timezone.now() - timedelta(days=i+15),
                venue='Test Arena',
                status='FINISHED',
                home_score=100,
                away_score=102
            )
            
            # Create player game stats with lower efficiency in older games
            PlayerGameStats.objects.create(
                player=self.player,
                game=game,
                points=20,
                rebounds=5,
                assists=4,
                steals=1,
                blocks=0,
                turnovers=3,
                minutes_played=30,
                field_goals_made=8,
                field_goals_attempted=18,
                three_pointers_made=1,
                three_pointers_attempted=4,
                free_throws_made=3,
                free_throws_attempted=4,
                efficiency=18.0
            )
        
        # Test trend calculation
        trend, rating = self.analytics.calculate_trend(days=30)
        self.assertIn(trend, ['IMPROVING', 'DECLINING', 'STABLE'])
        self.assertIsInstance(rating, float)
        
        # With our setup, we'd expect the trend to be IMPROVING
        self.assertEqual(trend, 'IMPROVING')


class TeamAnalyticsModelTests(TestCase):
    """Test cases for TeamAnalytics model methods"""
    
    def setUp(self):
        """Set up test data"""
        # Create teams
        self.team = Team.objects.create(
            name='Test Team',
            home_venue='Test Arena',
            founded_year=2000
        )
        
        # Create team analytics
        self.analytics = TeamAnalytics.objects.create(
            team=self.team,
            date=timezone.now().date(),
            wins=42,
            losses=24,
            points_scored_avg=108.5,
            points_allowed_avg=102.3,
            win_percentage=63.6
        )
    
    def test_team_analytics_str(self):
        """Test the TeamAnalytics __str__ method"""
        expected_str = f"{self.team.name} Analytics - {timezone.now().date()}"
        self.assertEqual(str(self.analytics), expected_str)


class GamePredictionModelTests(TestCase):
    """Test cases for GamePrediction model methods and calculations"""
    
    def setUp(self):
        """Set up test data"""
        # Create teams
        self.home_team = Team.objects.create(
            name='Home Team',
            home_venue='Home Arena',
            founded_year=2000
        )
        
        self.away_team = Team.objects.create(
            name='Away Team',
            home_venue='Away Arena',
            founded_year=2001
        )
        
        # Create a game
        self.game = Game.objects.create(
            home_team=self.home_team,
            away_team=self.away_team,
            date_time=timezone.now() + timedelta(days=1),
            venue='Home Arena',
            status='SCHEDULED'
        )
        
        # Create team analytics for both teams
        TeamAnalytics.objects.create(
            team=self.home_team,
            date=timezone.now().date(),
            wins=42,
            losses=24,
            points_scored_avg=108.5,
            points_allowed_avg=102.3,
            win_percentage=63.6
        )
        
        TeamAnalytics.objects.create(
            team=self.away_team,
            date=timezone.now().date(),
            wins=36,
            losses=30,
            points_scored_avg=105.2,
            points_allowed_avg=104.8,
            win_percentage=54.5
        )
        
        # Create players for both teams
        self.home_player = Player.objects.create(
            name='Home Player',
            team=self.home_team,
            position='PG',
            jersey_number=1
        )
        
        self.away_player = Player.objects.create(
            name='Away Player',
            team=self.away_team,
            position='PG',
            jersey_number=2
        )
        
        # Create player analytics
        PlayerAnalytics.objects.create(
            player=self.home_player,
            date=timezone.now().date(),
            points_avg=18.5,
            rebounds_avg=3.2,
            assists_avg=7.8,
            efficiency_rating=22.5
        )
        
        PlayerAnalytics.objects.create(
            player=self.away_player,
            date=timezone.now().date(),
            points_avg=20.1,
            rebounds_avg=4.0,
            assists_avg=6.2,
            efficiency_rating=21.8
        )
        
        # Create a game prediction
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
    
    def test_calculate_win_probability(self):
        """Test the win probability calculation"""
        win_prob = self.prediction.calculate_win_probability()
        self.assertIsInstance(win_prob, float)
        self.assertTrue(0 <= win_prob <= 100)
        
        # Home team has better record and home court advantage, so probability should be > 50%
        self.assertGreater(win_prob, 50.0)
    
    def test_evaluate_accuracy(self):
        """Test the evaluation of prediction accuracy"""
        # Change game to finished with actual results
        self.game.status = 'FINISHED'
        self.game.home_score = 108
        self.game.away_score = 100
        self.game.save()
        
        # Evaluate accuracy
        accuracy = self.prediction.evaluate_accuracy(self.game.home_score, self.game.away_score)
        self.assertIsInstance(accuracy, float)
        self.assertTrue(0 <= accuracy <= 100)
        
        # Since our prediction was home team win and actual result was home team win,
        # winner prediction was correct (40% of score), and scores were close (high percentage of remaining 60%)
        self.assertGreater(accuracy, 70.0)
        
        # Test with incorrect winner prediction
        wrong_accuracy = self.prediction.evaluate_accuracy(98, 105)
        
        # Since our prediction was home team win but actual result was away team win,
        # winner prediction was wrong (0% of 40%), only score accuracy contributes
        self.assertLess(wrong_accuracy, 60.0)


class PlayerPerformancePredictionTests(TestCase):
    """Test cases for PlayerPerformancePrediction model methods"""
    
    def setUp(self):
        """Set up test data"""
        # Create teams
        self.team = Team.objects.create(
            name='Test Team',
            home_venue='Test Arena',
            founded_year=2000
        )
        
        self.opponent = Team.objects.create(
            name='Opponent',
            home_venue='Away Arena',
            founded_year=2001
        )
        
        # Create a player
        self.player = Player.objects.create(
            name='Test Player',
            team=self.team,
            position='SG',
            jersey_number=23
        )
        
        # Create a future game
        self.game = Game.objects.create(
            home_team=self.team,
            away_team=self.opponent,
            date_time=timezone.now() + timedelta(days=1),
            venue='Test Arena',
            status='SCHEDULED'
        )
        
        # Create past games and stats to base prediction on
        for i in range(5):
            past_game = Game.objects.create(
                home_team=self.team,
                away_team=self.opponent,
                date_time=timezone.now() - timedelta(days=i*7),
                venue='Test Arena',
                status='FINISHED',
                home_score=100 + i,
                away_score=95 - i
            )
            
            # Create player stats
            PlayerGameStats.objects.create(
                player=self.player,
                game=past_game,
                points=20 + i,
                rebounds=5,
                assists=4,
                steals=1,
                blocks=0,
                turnovers=2,
                minutes_played=32,
                field_goals_made=8,
                field_goals_attempted=15,
                three_pointers_made=2,
                three_pointers_attempted=5,
                free_throws_made=2,
                free_throws_attempted=3
            )
        
        # Create prediction
        self.prediction = PlayerPerformancePrediction.objects.create(
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
    
    def test_calculate_prediction(self):
        """Test the prediction calculation"""
        prediction_data = self.prediction.calculate_prediction()
        self.assertIsInstance(prediction_data, dict)
        self.assertIn('points', prediction_data)
        self.assertIn('rebounds', prediction

