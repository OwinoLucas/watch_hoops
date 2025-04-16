from django.db import models
from django.utils import timezone
from django.db.models import Avg, Count, Sum, F, Q
from games.models import Game, MatchStats
from players.models import Player
from teams.models import Team
import json
import math

class PlayerAnalytics(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='analytics')
    date = models.DateField(default=timezone.now)
    points_avg = models.DecimalField(max_digits=5, decimal_places=2)
    rebounds_avg = models.DecimalField(max_digits=5, decimal_places=2)
    assists_avg = models.DecimalField(max_digits=5, decimal_places=2)
    efficiency_rating = models.DecimalField(max_digits=5, decimal_places=2)
    # New fields for shooting statistics
    field_goal_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    three_point_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    free_throw_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    true_shooting_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    # Additional performance metrics
    steals_avg = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    blocks_avg = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    turnovers_avg = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    minutes_avg = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    # Performance trend indicators
    last_10_games_rating = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    trend_direction = models.CharField(max_length=10, choices=[
        ('IMPROVING', 'Improving'),
        ('DECLINING', 'Declining'),
        ('STABLE', 'Stable'),
    ], default='STABLE')
    
    class Meta:
        unique_together = ['player', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.player.name} Analytics - {self.date}"
        
    def calculate_true_shooting(self):
        """Calculate true shooting percentage"""
        # TS% = Points / (2 * (FGA + (0.44 * FTA)))
        stats = PlayerGameStats.objects.filter(player=self.player).order_by('-game__date_time')[:10]
        if not stats:
            return 0.0
            
        total_points = sum(s.points for s in stats)
        total_fga = sum(s.field_goals_attempted for s in stats)
        total_fta = sum(s.free_throws_attempted for s in stats)
        
        if total_fga == 0 and total_fta == 0:
            return 0.0
            
        denominator = 2 * (total_fga + (0.44 * total_fta))
        if denominator == 0:
            return 0.0
            
        return round((total_points / denominator) * 100, 2)
        
    def calculate_trend(self, days=30):
        """Calculate performance trend over specified days"""
        # Compare recent games to the period before them
        now = timezone.now().date()
        mid_point = now - timezone.timedelta(days=days//2)
        start_date = now - timezone.timedelta(days=days)
        
        recent_stats = PlayerGameStats.objects.filter(
            player=self.player, 
            game__date_time__date__gte=mid_point,
            game__date_time__date__lte=now
        )
        
        older_stats = PlayerGameStats.objects.filter(
            player=self.player,
            game__date_time__date__gte=start_date,
            game__date_time__date__lt=mid_point
        )
        
        if not recent_stats or not older_stats:
            return 'STABLE', 0.0
            
        recent_efficiency = sum(s.efficiency for s in recent_stats) / recent_stats.count() if recent_stats.count() > 0 else 0
        older_efficiency = sum(s.efficiency for s in older_stats) / older_stats.count() if older_stats.count() > 0 else 0
        
        if recent_efficiency > older_efficiency * 1.1:
            return 'IMPROVING', recent_efficiency
        elif recent_efficiency < older_efficiency * 0.9:
            return 'DECLINING', recent_efficiency
        else:
            return 'STABLE', recent_efficiency

class PlayerPerformancePrediction(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='performance_predictions')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='player_predictions')
    predicted_points = models.IntegerField()
    predicted_rebounds = models.IntegerField()
    predicted_assists = models.IntegerField()
    predicted_steals = models.IntegerField(default=0)
    predicted_blocks = models.IntegerField(default=0)
    predicted_minutes = models.IntegerField(default=0)
    predicted_efficiency = models.DecimalField(max_digits=5, decimal_places=2)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, help_text="0-100 confidence level")
    factors = models.JSONField(default=dict, help_text="Factors influencing the prediction")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-game__date_time', '-created_at']
        unique_together = ['player', 'game']
        
    def __str__(self):
        return f"Prediction for {self.player.name} in {self.game}"
    
    def calculate_prediction(self):
        """Calculate prediction based on historical data"""
        # Get recent games against the same opponent
        opponent = self.game.home_team if self.game.away_team == self.player.team else self.game.away_team
        
        # Get player stats from last 5 games against this opponent
        vs_opponent_stats = PlayerGameStats.objects.filter(
            player=self.player,
            game__home_team=opponent
        ).order_by('-game__date_time')[:5]
        
        # Get player stats from last 10 games overall
        recent_stats = PlayerGameStats.objects.filter(
            player=self.player
        ).order_by('-game__date_time')[:10]
        
        # Calculate predictions based on weighted average
        if not recent_stats:
            return {
                'points': 0,
                'rebounds': 0,
                'assists': 0,
                'steals': 0,
                'blocks': 0,
                'minutes': 0,
                'efficiency': 0.0,
                'confidence': 0.0
            }
            
        # Calculate recent averages
        recent_avg = {
            'points': sum(s.points for s in recent_stats) / len(recent_stats),
            'rebounds': sum(s.rebounds for s in recent_stats) / len(recent_stats),
            'assists': sum(s.assists for s in recent_stats) / len(recent_stats),
            'steals': sum(s.steals for s in recent_stats) / len(recent_stats),
            'blocks': sum(s.blocks for s in recent_stats) / len(recent_stats),
            'minutes': sum(s.minutes_played for s in recent_stats) / len(recent_stats),
        }
        
        # If we have stats against this opponent, weight them more heavily
        if vs_opponent_stats:
            vs_opp_avg = {
                'points': sum(s.points for s in vs_opponent_stats) / len(vs_opponent_stats),
                'rebounds': sum(s.rebounds for s in vs_opponent_stats) / len(vs_opponent_stats),
                'assists': sum(s.assists for s in vs_opponent_stats) / len(vs_opponent_stats),
                'steals': sum(s.steals for s in vs_opponent_stats) / len(vs_opponent_stats),
                'blocks': sum(s.blocks for s in vs_opponent_stats) / len(vs_opponent_stats),
                'minutes': sum(s.minutes_played for s in vs_opponent_stats) / len(vs_opponent_stats),
            }
            
            # Weight: 70% vs opponent, 30% recent overall
            prediction = {
                'points': int((vs_opp_avg['points'] * 0.7) + (recent_avg['points'] * 0.3)),
                'rebounds': int((vs_opp_avg['rebounds'] * 0.7) + (recent_avg['rebounds'] * 0.3)),
                'assists': int((vs_opp_avg['assists'] * 0.7) + (recent_avg['assists'] * 0.3)),
                'steals': int((vs_opp_avg['steals'] * 0.7) + (recent_avg['steals'] * 0.3)),
                'blocks': int((vs_opp_avg['blocks'] * 0.7) + (recent_avg['blocks'] * 0.3)),
                'minutes': int((vs_opp_avg['minutes'] * 0.7) + (recent_avg['minutes'] * 0.3)),
                'confidence': 75.0  # Higher confidence with opponent data
            }
        else:
            # Just use recent averages with lower confidence
            prediction = {
                'points': int(recent_avg['points']),
                'rebounds': int(recent_avg['rebounds']),
                'assists': int(recent_avg['assists']),
                'steals': int(recent_avg['steals']),
                'blocks': int(recent_avg['blocks']),
                'minutes': int(recent_avg['minutes']),
                'confidence': 50.0  # Lower confidence without opponent data
            }
        
        # Calculate efficiency
        prediction['efficiency'] = round((
            prediction['points'] + 
            prediction['rebounds'] * 1.2 + 
            prediction['assists'] * 1.5 + 
            prediction['steals'] * 2 + 
            prediction['blocks'] * 2
        ) / prediction['minutes'] * 10, 2) if prediction['minutes'] > 0 else 0.0
        
        return prediction
        
    def save_prediction(self):
        """Calculate and save the prediction values"""
        prediction = self.calculate_prediction()
        
        self.predicted_points = prediction['points']
        self.predicted_rebounds = prediction['rebounds']
        self.predicted_assists = prediction['assists']
        self.predicted_steals = prediction['steals']
        self.predicted_blocks = prediction['blocks']
        self.predicted_minutes = prediction['minutes']
        self.predicted_efficiency = prediction['efficiency']
        self.confidence_score = prediction['confidence']
        
        # Save factors influencing prediction
        factors = {
            'recent_form': 'good' if prediction['efficiency'] > 15 else 'average' if prediction['efficiency'] > 10 else 'poor',
            'matchup_history': 'favorable' if prediction['confidence'] > 70 else 'neutral' if prediction['confidence'] > 50 else 'unfavorable',
            'minutes_projection': 'high' if prediction['minutes'] > 30 else 'moderate' if prediction['minutes'] > 20 else 'low',
        }
        
        self.factors = factors
        self.save()

class TeamAnalytics(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='analytics')
    date = models.DateField(default=timezone.now)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    points_scored_avg = models.DecimalField(max_digits=5, decimal_places=2)
    points_allowed_avg = models.DecimalField(max_digits=5, decimal_places=2)
    win_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    
    class Meta:
        unique_together = ['team', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.team.name} Analytics - {self.date}"

class GamePrediction(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='predictions')
    home_team_win_probability = models.DecimalField(max_digits=5, decimal_places=2)
    predicted_home_score = models.IntegerField()
    predicted_away_score = models.IntegerField()
    # Quarter-by-quarter score predictions
    home_q1_score = models.IntegerField(default=0)
    home_q2_score = models.IntegerField(default=0)
    home_q3_score = models.IntegerField(default=0)
    home_q4_score = models.IntegerField(default=0)
    away_q1_score = models.IntegerField(default=0)
    away_q2_score = models.IntegerField(default=0)
    away_q3_score = models.IntegerField(default=0)
    away_q4_score = models.IntegerField(default=0)
    # Key matchup factors
    key_matchup_factors = models.JSONField(default=dict, help_text="Factors influencing the game prediction")
    prediction_accuracy = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Post-game accuracy of prediction")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Prediction for {self.game}"

    def calculate_win_probability(self):
        """Calculate win probability based on team matchups and recent form"""
        home_team = self.game.home_team
        away_team = self.game.away_team
        
        # Get recent team analytics
        try:
            home_analytics = TeamAnalytics.objects.filter(team=home_team).latest('date')
            away_analytics = TeamAnalytics.objects.filter(team=away_team).latest('date')
        except TeamAnalytics.DoesNotExist:
            # Default to 50% if no analytics available
            return 50.0

        # Factor 1: Overall team strength (win percentage)
        home_strength = float(home_analytics.win_percentage)
        away_strength = float(away_analytics.win_percentage)
        
        # Factor 2: Home court advantage (typically ~60% in basketball)
        home_advantage = 10.0
        
        # Factor 3: Recent form - get last 5 games results
        home_recent_games = Game.objects.filter(
            Q(home_team=home_team) | Q(away_team=home_team)
        ).order_by('-date_time')[:5]
        
        away_recent_games = Game.objects.filter(
            Q(home_team=away_team) | Q(away_team=away_team)
        ).order_by('-date_time')[:5]
        
        # Calculate recent win percentage
        home_recent_wins = sum(1 for g in home_recent_games if 
                            (g.home_team == home_team and g.home_score > g.away_score) or 
                            (g.away_team == home_team and g.away_score > g.home_score))
        
        away_recent_wins = sum(1 for g in away_recent_games if 
                            (g.home_team == away_team and g.home_score > g.away_score) or 
                            (g.away_team == away_team and g.away_score > g.home_score))
        
        home_recent_form = (home_recent_wins / len(home_recent_games)) * 100 if home_recent_games else 50
        away_recent_form = (away_recent_wins / len(away_recent_games)) * 100 if away_recent_games else 50
        
        # Factor 4: Head-to-head history
        h2h_games = Game.objects.filter(
            (Q(home_team=home_team) & Q(away_team=away_team)) | 
            (Q(home_team=away_team) & Q(away_team=home_team))
        ).order_by('-date_time')[:5]
        
        home_h2h_wins = sum(1 for g in h2h_games if 
                          (g.home_team == home_team and g.home_score > g.away_score) or 
                          (g.away_team == home_team and g.away_score > g.home_score))
        
        h2h_advantage = 0
        if h2h_games:
            h2h_win_pct = (home_h2h_wins / len(h2h_games)) * 100
            h2h_advantage = h2h_win_pct - 50  # Advantage relative to 50%
        
        # Calculate final probability - weight the factors
        win_probability = (
            (home_strength - away_strength) * 0.3 +  # 30% weight to season record difference
            home_advantage +                         # Home court advantage
            (home_recent_form - away_recent_form) * 0.4 +  # 40% weight to recent form
            h2h_advantage * 0.2                     # 20% weight to head-to-head
        ) + 50  # Add to baseline 50%
        
        # Ensure probability is between 0 and 100
        return max(0, min(100, win_probability))
    
    def predict_quarter_scores(self):
        """Predict quarter-by-quarter scores based on team analytics"""
        home_team = self.game.home_team
        away_team = self.game.away_team
        
        # Get recent games to analyze scoring patterns
        home_games = Game.objects.filter(
            Q(home_team=home_team) | Q(away_team=home_team)
        ).order_by('-date_time')[:10]
        
        away_games = Game.objects.filter(
            Q(home_team=away_team) | Q(away_team=away_team)
        ).order_by('-date_time')[:10]
        
        if not home_games or not away_games:
            # Default distribution if no data
            self.home_q1_score = self.predicted_home_score // 4
            self.home_q2_score = self.predicted_home_score // 4
            self.home_q3_score = self.predicted_home_score // 4
            self.home_q4_score = self.predicted_home_score - (self.home_q1_score + self.home_q2_score + self.home_q3_score)
            
            self.away_q1_score = self.predicted_away_score // 4
            self.away_q2_score = self.predicted_away_score // 4
            self.away_q3_score = self.predicted_away_score // 4
            self.away_q4_score = self.predicted_away_score - (self.away_q1_score + self.away_q2_score + self.away_q3_score)
            return
        
        # Calculate average quarter scoring patterns
        home_q1_pct = 0.25  # Default to even distribution
        home_q2_pct = 0.25
        home_q3_pct = 0.25
        home_q4_pct = 0.25
        
        away_q1_pct = 0.25
        away_q2_pct = 0.25
        away_q3_pct = 0.25
        away_q4_pct = 0.25
        
        # TODO: Calculate actual percentages from game data when quarter stats are available
        # For now using estimated distributions based on team tendencies
        
        # Apply percentages to total predicted score
        self.home_q1_score = int(self.predicted_home_score * home_q1_pct)
        self.home_q2_score = int(self.predicted_home_score * home_q2_pct)
        self.home_q3_score = int(self.predicted_home_score * home_q3_pct)
        self.home_q4_score = self.predicted_home_score - (self.home_q1_score + self.home_q2_score + self.home_q3_score)
        
        self.away_q1_score = int(self.predicted_away_score * away_q1_pct)
        self.away_q2_score = int(self.predicted_away_score * away_q2_pct)
        self.away_q3_score = int(self.predicted_away_score * away_q3_pct)
        self.away_q4_score = self.predicted_away_score - (self.away_q1_score + self.away_q2_score + self.away_q3_score)
    
    def identify_key_matchups(self):
        """Identify key player matchups that will influence the game"""
        home_team = self.game.home_team
        away_team = self.game.away_team
        
        # Get top players from each team
        home_players = Player.objects.filter(team=home_team)
        away_players = Player.objects.filter(team=away_team)
        
        key_matchups = []
        
        # Get player analytics for comparison
        for home_player in home_players[:3]:  # Top 3 players
            try:
                home_analytics = PlayerAnalytics.objects.filter(player=home_player).latest('date')
                
                # Find matching position player on away team
                for away_player in away_players:
                    if away_player.position == home_player.position:
                        try:
                            away_analytics = PlayerAnalytics.objects.filter(player=away_player).latest('date')
                            
                            # Compare player stats to determine matchup advantage
                            home_rating = float(home_analytics.efficiency_rating)
                            away_rating = float(away_analytics.efficiency_rating)
                            
                            advantage = ''
                            if home_rating > away_rating * 1.2:
                                advantage = 'strong_home'
                            elif home_rating > away_rating * 1.05:
                                advantage = 'slight_home'
                            elif away_rating > home_rating * 1.2:
                                advantage = 'strong_away'
                            elif away_rating > home_rating * 1.05:
                                advantage = 'slight_away'
                            else:
                                advantage = 'even'
                                
                            key_matchups.append({
                                'home_player': {
                                    'id': home_player.id,
                                    'name': home_player.name,
                                    'position': home_player.position,
                                    'efficiency': float(home_analytics.efficiency_rating)
                                },
                                'away_player': {
                                    'id': away_player.id,
                                    'name': away_player.name,
                                    'position': away_player.position,
                                    'efficiency': float(away_analytics.efficiency_rating)
                                },
                                'advantage': advantage,
                                'impact_level': 'high' if max(home_rating, away_rating) > 20 else 'medium' if max(home_rating, away_rating) > 15 else 'low'
                            })
                            break  # Found a matchup for this player
                        except PlayerAnalytics.DoesNotExist:
                            continue
            except PlayerAnalytics.DoesNotExist:
                continue
                
        self.key_matchup_factors = {
            'key_player_matchups': key_matchups[:3],  # Keep only top 3 important matchups
            'home_advantage': 'strong' if self.home_team_win_probability > 65 else 'moderate' if self.home_team_win_probability > 55 else 'slight' if self.home_team_win_probability > 50 else 'none',
            'predicted_pace': 'fast' if (self.predicted_home_score + self.predicted_away_score) > 220 else 'moderate' if (self.predicted_home_score + self.predicted_away_score) > 200 else 'slow',
        }
        
    def calculate_prediction(self):
        """Calculate overall game prediction, including quarter scores and matchup factors"""
        # Calculate win probability
        self.home_team_win_probability = self.calculate_win_probability()
        
        # Set predicted total scores
        # This simplified model uses team analytics averages modified by win probability
        try:
            home_analytics = TeamAnalytics.objects.filter(team=self.game.home_team).latest('date')
            away_analytics = TeamAnalytics.objects.filter(team=self.game.away_team).latest('date')
            
            # Base predicted scores on season averages
            self.predicted_home_score = int(float(home_analytics.points_scored_avg))
            self.predicted_away_score = int(float(away_analytics.points_scored_avg))
            
            # Adjust scores based on win probability (higher win probability should mean higher score differential)
            projected_margin = (self.home_team_win_probability - 50) / 2.5  # Each 2.5% over 50% = 1 point
            
            self.predicted_home_score = max(70, int(self.predicted_home_score + projected_margin / 2))
            self.predicted_away_score = max(70, int(self.predicted_away_score - projected_margin / 2))
            
        except TeamAnalytics.DoesNotExist:
            # Fallback defaults if team analytics are missing
            self.predicted_home_score = 100
            self.predicted_away_score = 100
            
            if self.home_team_win_probability > 50:
                margin = (self.home_team_win_probability - 50) / 5
                self.predicted_home_score += int(margin)
                self.predicted_away_score -= int(margin)
            else:
                margin = (50 - self.home_team_win_probability) / 5
                self.predicted_home_score -= int(margin)
                self.predicted_away_score += int(margin)
        
        # Calculate quarter-by-quarter scores
        self.predict_quarter_scores()
        
        # Identify key matchups
        self.identify_key_matchups()
        
        self.save()
        
    def evaluate_accuracy(self, actual_home_score, actual_away_score):
        """Evaluate prediction accuracy after the game is complete"""
        if actual_home_score is None or actual_away_score is None:
            return None
            
        # Predicted winner accuracy
        predicted_winner_home = self.home_team_win_probability > 50
        actual_winner_home = actual_home_score > actual_away_score
        
        winner_correct = predicted_winner_home == actual_winner_home
        
        # Score prediction accuracy (as percentage of total score)
        total_actual = actual_home_score + actual_away_score
        home_diff = abs(self.predicted_home_score - actual_home_score)
        away_diff = abs(self.predicted_away_score - actual_away_score)
        total_error = (home_diff + away_diff) / total_actual
        
        score_accuracy = 100 * (1 - total_error)
        
        # Overall accuracy - weight winner prediction at 40%, score at 60%
        overall_accuracy = (winner_correct * 40) + (score_accuracy * 0.6)
        
        self.prediction_accuracy = overall_accuracy
        self.save()
        
        return overall_accuracy


class TeamPerformanceTrend(models.Model):
    """Model for tracking team performance trends over time periods"""
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='performance_trends')
    period_start = models.DateField()
    period_end = models.DateField()
    period_type = models.CharField(max_length=20, choices=[
        ('WEEK', 'Week'),
        ('MONTH', 'Month'),
        ('SEASON', 'Season'),
        ('CUSTOM', 'Custom'),
    ])
    
    # Overall performance metrics
    games_played = models.IntegerField(default=0)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    points_scored_avg = models.DecimalField(max_digits=5, decimal_places=2)
    points_allowed_avg = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Quarter-by-quarter performance
    q1_points_scored_avg = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    q2_points_scored_avg = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    q3_points_scored_avg = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    q4_points_scored_avg = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    q1_points_allowed_avg = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    q2_points_allowed_avg = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    q3_points_allowed_avg = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    q4_points_allowed_avg = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Home/away splits
    home_wins = models.IntegerField(default=0)
    home_losses = models.IntegerField(default=0)
    away_wins = models.IntegerField(default=0)
    away_losses = models.IntegerField(default=0)
    home_points_scored_avg = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    home_points_allowed_avg = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    away_points_scored_avg = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    away_points_allowed_avg = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Team form indicators
    streak_type = models.CharField(max_length=4, choices=[
        ('WIN', 'Win'),
        ('LOSS', 'Loss'),
    ], null=True, blank=True)
    streak_count = models.IntegerField(default=0)
    trend_direction = models.CharField(max_length=10, choices=[
        ('IMPROVING', 'Improving'),
        ('DECLINING', 'Declining'),
        ('STABLE', 'Stable'),
    ], default='STABLE')
    
    # Team efficiency metrics
    offensive_efficiency = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    defensive_efficiency = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    pace = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Estimated possessions per game")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-period_end', 'team']
        unique_together = ['team', 'period_start', 'period_end', 'period_type']
        
    def __str__(self):
        return f"{self.team.name} Trend ({self.period_type}): {self.period_start} to {self.period_end}"
    
    def calculate_trend(self):
        """Calculate performance trends based on games in the period"""
        games = Game.objects.filter(
            Q(home_team=self.team) | Q(away_team=self.team),
            date_time__date__gte=self.period_start,
            date_time__date__lte=self.period_end
        ).order_by('date_time')
        
        if not games:
            return
            
        self.games_played = len(games)
        
        # Calculate wins and losses
        self.wins = 0
        self.losses = 0
        self.home_wins = 0
        self.home_losses = 0
        self.away_wins = 0
        self.away_losses = 0
        
        total_points_scored = 0
        total_points_allowed = 0
        home_points_scored = 0
        home_points_allowed = 0
        away_points_scored = 0
        away_points_allowed = 0
        
        # TODO: Add quarter-by-quarter analysis when that data is available
        # For now, using simple averages
        
        # Calculate streak
        current_streak_type = None
        current_streak_count = 0
        
        for game in games:
            is_home = game.home_team == self.team
            
            # Calculate points scored and allowed
            if is_home:
                team_score = game.home_score
                opponent_score = game.away_score
                home_points_scored += team
