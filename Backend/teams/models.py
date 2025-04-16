from django.db import models
from typing import List, Dict, Any, Optional
from django.db.models import Q, Sum, Count, Avg, F

class League(models.Model):
    """
    Represents a basketball league.
    
    This model stores information about basketball leagues, including:
    - League name and country
    - Logo image
    - Creation and update timestamps
    
    A league contains multiple teams and hosts multiple games.
    
    Related models:
    - Team: Teams that participate in this league
    - games.Game: Games played in this league
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Name of the league"
    )
    country = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Country where the league operates"
    )
    logo = models.ImageField(
        upload_to='league_logos/', 
        null=True, 
        blank=True,
        help_text="Logo image for the league"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of the league"
    )
    season_start = models.DateField(
        null=True,
        blank=True,
        help_text="Start date of the current season"
    )
    season_end = models.DateField(
        null=True,
        blank=True,
        help_text="End date of the current season"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "League"
        verbose_name_plural = "Leagues"
        ordering = ['name']
        indexes = [
            models.Index(fields=['country', 'name']),
        ]
    
    def __str__(self) -> str:
        """Return a string representation of the league."""
        return self.name
    
    def get_teams_count(self) -> int:
        """
        Get the number of teams in this league.
        
        Returns:
            int: Number of teams in the league
        """
        return self.teams.count()
    
    def get_active_teams(self):
        """
        Get all active teams in this league.
        
        Returns:
            QuerySet: Active teams in the league
        """
        return self.teams.filter(is_active=True)
    
    def get_current_standings(self) -> List[Dict[str, Any]]:
        """
        Get the current standings for the league.
        
        Returns:
            List[Dict]: List of teams with their win/loss records, ordered by win percentage
        """
        teams = self.teams.all()
        standings = []
        
        for team in teams:
            standings.append({
                'team': team,
                'wins': team.get_wins_count(),
                'losses': team.get_losses_count(),
                'win_percentage': team.get_win_percentage(),
            })
        
        return sorted(standings, key=lambda x: x['win_percentage'], reverse=True)


class Team(models.Model):
    """
    Represents a basketball team.
    
    This model stores information about basketball teams, including:
    - Team name and logo
    - League affiliation
    - Home venue
    - Team statistics
    
    A team has multiple players and participates in games.
    
    Related models:
    - League: The league this team belongs to
    - games.Game: Games this team participates in (as home_team or away_team)
    - players.Player: Players who are members of this team
    """
    name = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Name of the team"
    )
    league = models.ForeignKey(
        League, 
        on_delete=models.CASCADE,
        related_name='teams',
        help_text="League this team belongs to"
    )
    logo = models.ImageField(
        upload_to='team_logos/',
        null=True, 
        blank=True,
        help_text="Logo image for the team"
    )
    founded_year = models.IntegerField(
        null=True,
        blank=True,
        help_text="Year the team was founded"
    )
    home_venue = models.CharField(
        max_length=200,
        help_text="Home venue where the team plays"
    )
    description = models.TextField(
        blank=True,
        help_text="Description or history of the team"
    )
    website = models.URLField(
        blank=True,
        help_text="Official team website"
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether the team is currently active"
    )
    team_colors = models.CharField(
        max_length=100,
        blank=True,
        help_text="Team colors (e.g., 'Red, White, Blue')"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Team"
        verbose_name_plural = "Teams"
        ordering = ['name']
        indexes = [
            models.Index(fields=['league', 'name']),
            models.Index(fields=['is_active']),
        ]
        unique_together = ['name', 'league']
    
    def __str__(self) -> str:
        """Return a string representation of the team."""
        return f"{self.name} ({self.league.name})"
    
    def get_wins_count(self) -> int:
        """
        Get the number of wins for this team.
        
        Returns:
            int: Number of wins
        """
        home_wins = self.home_matches.filter(
            status='FINISHED',
            home_score__gt=F('away_score')
        ).count()
        
        away_wins = self.away_matches.filter(
            status='FINISHED',
            away_score__gt=F('home_score')
        ).count()
        
        return home_wins + away_wins
    
    def get_losses_count(self) -> int:
        """
        Get the number of losses for this team.
        
        Returns:
            int: Number of losses
        """
        home_losses = self.home_matches.filter(
            status='FINISHED',
            home_score__lt=F('away_score')
        ).count()
        
        away_losses = self.away_matches.filter(
            status='FINISHED',
            away_score__lt=F('home_score')
        ).count()
        
        return home_losses + away_losses
    
    def get_win_percentage(self) -> float:
        """
        Calculate win percentage for this team.
        
        Returns:
            float: Win percentage (0.0 to 1.0)
        """
        wins = self.get_wins_count()
        losses = self.get_losses_count()
        
        if wins + losses == 0:
            return 0.0
        
        return wins / (wins + losses)
    
    def get_roster(self, active_only: bool = True):
        """
        Get the current roster of players for this team.
        
        Args:
            active_only: Whether to only include active players
            
        Returns:
            QuerySet: Players on this team's roster
        """
        if active_only:
            return self.players.filter(is_active=True)
        return self.players.all()
    
    def get_upcoming_games(self, limit: Optional[int] = None):
        """
        Get upcoming games for this team.
        
        Args:
            limit: Optional limit on the number of games to return
            
        Returns:
            QuerySet: Upcoming games for this team
        """
        from django.utils import timezone
        
        upcoming_games = self.home_matches.filter(
            Q(status='SCHEDULED') | Q(status='POSTPONED'),
            date_time__gt=timezone.now()
        ).union(
            self.away_matches.filter(
                Q(status='SCHEDULED') | Q(status='POSTPONED'),
                date_time__gt=timezone.now()
            )
        ).order_by('date_time')
        
        if limit:
            return upcoming_games[:limit]
        return upcoming_games
    
    def get_recent_games(self, limit: Optional[int] = 5):
        """
        Get recent games for this team.
        
        Args:
            limit: Number of recent games to return (default: 5)
            
        Returns:
            QuerySet: Recent games for this team
        """
        recent_games = self.home_matches.filter(
            status='FINISHED'
        ).union(
            self.away_matches.filter(
                status='FINISHED'
            )
        ).order_by('-date_time')
        
        return recent_games[:limit]
    
    def get_team_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics for this team.
        
        Returns:
            Dict: Dictionary containing team statistics
        """
        from django.db.models import Avg
        
        # Get team game statistics
        home_games = self.home_matches.filter(status='FINISHED')
        away_games = self.away_matches.filter(status='FINISHED')
        
        total_games = home_games.count() + away_games.count()
        
        # Calculate average points scored and conceded
        avg_points_scored_home = home_games.aggregate(avg=Avg('home_score'))['avg'] or 0
        avg_points_scored_away = away_games.aggregate(avg=Avg('away_score'))['avg'] or 0
        
        avg_points_conceded_home = home_games.aggregate(avg=Avg('away_score'))['avg'] or 0
        avg_points_conceded_away = away_games.aggregate(avg=Avg('home_score'))['avg'] or 0
        
        # Calculate record
        wins = self.get_wins_count()
        losses = self.get_losses_count()
        
        # Calculate home and away records
        home_wins = home_games.filter(home_score__gt=F('away_score')).count()
        home_losses = home_games.filter(home_score__lt=F('away_score')).count()
        
        away_wins = away_games.filter(away_score__gt=F('home_score')).count()
        away_losses = away_games.filter(away_score__lt=F('home_score')).count()
        
        return {
            'record': f"{wins}-{losses}",
            'win_percentage': self.get_win_percentage(),
            'home_record': f"{home_wins}-{home_losses}",
            'away_record': f"{away_wins}-{away_losses}",
            'total_games': total_games,
            'avg_points_scored': (avg_points_scored_home * home_games.count() + 
                                 avg_points_scored_away * away_games.count()) / max(total_games, 1),
            'avg_points_conceded': (avg_points_conceded_home * home_games.count() + 
                                   avg_points_conceded_away * away_games.count()) / max(total_games, 1),
        }
