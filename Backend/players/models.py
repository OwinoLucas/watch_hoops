from django.db import models
from django.utils import timezone
from typing import Dict, List, Any, Optional, Tuple
from django.db.models import Avg, Sum, Count, F, Q

class Player(models.Model):
    """
    Represents a basketball player.
    
    This model stores comprehensive information about basketball players, including:
    - Personal information and biometrics
    - Career statistics and achievements
    - Team affiliation history
    - Current status
    
    A player is linked to a CustomUser account and belongs to a team.
    
    Related models:
    - accounts.CustomUser: User account linked to this player
    - teams.Team: The team this player belongs to
    - games.MatchStats: Player statistics for individual games
    - PlayerTeamHistory: History of team affiliations
    """
    POSITIONS = (
        ('PG', 'Point Guard'),
        ('SG', 'Shooting Guard'),
        ('SF', 'Small Forward'),
        ('PF', 'Power Forward'),
        ('C', 'Center'),
    )
    
    # Personal Information
    user = models.OneToOneField(
        'accounts.CustomUser', 
        on_delete=models.CASCADE,
        related_name='player_profile',
        help_text="User account linked to this player"
    )
    
    team = models.ForeignKey(
        'teams.Team', 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        related_name='players',
        help_text="Current team of the player"
    )
    
    position = models.CharField(
        max_length=2, 
        choices=POSITIONS,
        db_index=True,
        help_text="Primary playing position"
    )
    
    secondary_position = models.CharField(
        max_length=2, 
        choices=POSITIONS,
        null=True, 
        blank=True,
        help_text="Secondary playing position, if any"
    )
    
    jersey_number = models.PositiveSmallIntegerField(
        help_text="Player's jersey number"
    )
    
    # Biometric Data
    height_cm = models.PositiveSmallIntegerField(
        help_text="Height in centimeters"
    )
    weight_kg = models.PositiveSmallIntegerField(
        help_text="Weight in kilograms"
    )
    wingspan_cm = models.PositiveSmallIntegerField(
        null=True, 
        blank=True,
        help_text="Wingspan in centimeters, if known"
    )
    
    # Biographical Information
    date_of_birth = models.DateField(
        help_text="Player's date of birth"
    )
    nationality = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Player's nationality"
    )
    birthplace = models.CharField(
        max_length=200,
        help_text="Player's place of birth"
    )
    draft_year = models.PositiveSmallIntegerField(
        null=True, 
        blank=True,
        help_text="Year the player was drafted, if applicable"
    )
    draft_position = models.PositiveSmallIntegerField(
        null=True, 
        blank=True,
        help_text="Player's draft position, if applicable"
    )
    
    # Media and Bio
    profile_image = models.ImageField(
        upload_to='player_profiles/',
        null=True, 
        blank=True,
        help_text="Player's profile image"
    )
    biography = models.TextField(
        blank=True,
        help_text="Player's biography or career summary"
    )
    
    # Social Media
    twitter_handle = models.CharField(
        max_length=50, 
        blank=True,
        help_text="Player's Twitter handle"
    )
    instagram_handle = models.CharField(
        max_length=50, 
        blank=True,
        help_text="Player's Instagram handle"
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether the player is currently active"
    )
    is_injured = models.BooleanField(
        default=False,
        help_text="Whether the player is currently injured"
    )
    injury_details = models.CharField(
        max_length=255, 
        blank=True,
        help_text="Details about player's injury, if any"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Player"
        verbose_name_plural = "Players"
        ordering = ['team', 'user__last_name', 'user__first_name']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['team', 'is_active']),
            models.Index(fields=['position', 'is_active']),
            models.Index(fields=['nationality']),
        ]
    
    def __str__(self) -> str:
        """Return a string representation of the player."""
        return f"{self.user.get_full_name()} ({self.team.name if self.team else 'Free Agent'})"
    
    @property
    def age(self) -> int:
        """
        Calculate the player's current age.
        
        Returns:
            int: Player's age in years
        """
        today = timezone.now().date()
        born = self.date_of_birth
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    
    @property
    def height_ft_in(self) -> str:
        """
        Convert height from cm to feet and inches.
        
        Returns:
            str: Height in feet and inches format (e.g., "6'7")
        """
        total_inches = self.height_cm / 2.54
        feet = int(total_inches // 12)
        inches = int(total_inches % 12)
        return f"{feet}'{inches}\""
    
    @property
    def weight_lbs(self) -> int:
        """
        Convert weight from kg to lbs.
        
        Returns:
            int: Weight in pounds
        """
        return int(self.weight_kg * 2.20462)
    
    def get_career_statistics(self) -> Dict[str, Any]:
        """
        Calculate career statistics across all games.
        
        Returns:
            Dict: Dictionary containing career statistics
        """
        stats = self.match_stats.aggregate(
            games_played=Count('id'),
            total_points=Sum('points'),
            total_assists=Sum('assists'),
            total_rebounds=Sum('rebounds'),
            total_steals=Sum('steals'),
            total_blocks=Sum('blocks'),
            total_turnovers=Sum('turnovers'),
            total_minutes=Sum('minutes_played')
        )
        
        games_played = stats['games_played'] or 0
        
        if games_played > 0:
            stats['ppg'] = stats['total_points'] / games_played
            stats['apg'] = stats['total_assists'] / games_played
            stats['rpg'] = stats['total_rebounds'] / games_played
            stats['spg'] = stats['total_steals'] / games_played
            stats['bpg'] = stats['total_blocks'] / games_played
            stats['topg'] = stats['total_turnovers'] / games_played
            stats['mpg'] = stats['total_minutes'] / games_played
        else:
            stats.update({
                'ppg': 0, 'apg': 0, 'rpg': 0, 
                'spg': 0, 'bpg': 0, 'topg': 0, 'mpg': 0
            })
        
        return stats
    
    def get_season_statistics(self, season_start: Optional[str] = None, season_end: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate statistics for a specific season.
        
        Args:
            season_start: Start date of the season (format: 'YYYY-MM-DD')
            season_end: End date of the season (format: 'YYYY-MM-DD')
            
        Returns:
            Dict: Dictionary containing season statistics
        """
        if not season_start or not season_end:
            from django.utils import timezone
            now = timezone.now()
            current_year = now.year
            # Default to current season (roughly October to June)
            season_start = f"{current_year-1 if now.month < 10 else current_year}-10-01"
            season_end = f"{current_year}-06-30"
        
        season_stats = self.match_stats.filter(
            match__date_time__gte=season_start,
            match__date_time__lte=season_end
        ).aggregate(
            games_played=Count('id'),
            total_points=Sum('points'),
            total_assists=Sum('assists'),
            total_rebounds=Sum('rebounds'),
            total_steals=Sum('steals'),
            total_blocks=Sum('blocks'),
            total_turnovers=Sum('turnovers'),
            total_minutes=Sum('minutes_played')
        )
        
        games_played = season_stats['games_played'] or 0
        
        if games_played > 0:
            season_stats['ppg'] = season_stats['total_points'] / games_played
            season_stats['apg'] = season_stats['total_assists'] / games_played
            season_stats['rpg'] = season_stats['total_rebounds'] / games_played
            season_stats['spg'] = season_stats['total_steals'] / games_played
            season_stats['bpg'] = season_stats['total_blocks'] / games_played
            season_stats['topg'] = season_stats['total_turnovers'] / games_played
            season_stats['mpg'] = season_stats['total_minutes'] / games_played
        else:
            season_stats.update({
                'ppg': 0, 'apg': 0, 'rpg': 0, 
                'spg': 0, 'bpg': 0, 'topg': 0, 'mpg': 0
            })
        
        return season_stats
    
    def get_recent_games_stats(self, num_games: int = 5) -> List[Dict[str, Any]]:
        """
        Get statistics for player's recent games.
        
        Args:
            num_games: Number of recent games to include
            
        Returns:
            List[Dict]: List of dictionaries containing stats for each recent game
        """
        recent_stats = self.match_stats.order_by('-match__date_time')[:num_games]
        return list(recent_stats.values(
            'match__date_time', 
            'match__home_team__name', 
            'match__away_team__name',
            'points', 'assists', 'rebounds', 
            'steals', 'blocks', 'turnovers', 
            'minutes_played'
        ))
    
    def change_team(self, new_team: 'teams.Team', transfer_date: Optional[timezone.datetime] = None) -> None:
        """
        Change the player's team and record the transfer in history.
        
        Args:
            new_team: The team the player is transferring to
            transfer_date: Date of the transfer (defaults to now)
        """
        if not transfer_date:
            transfer_date = timezone.now()
        
        # Record the transfer in history if player already had a team
        if self.team:
            PlayerTeamHistory.objects.create(
                player=self,
                team=self.team,
                start_date=self.playerteamhistory_set.filter(
                    team=self.team
                ).first().start_date if self.playerteamhistory_set.filter(team=self.team).exists() else None,
                end_date=transfer_date
            )
        
        # Update to new team
        self.team = new_team
        self.save()
        
        # Create new history record
        PlayerTeamHistory.objects.create(
            player=self,
            team=new_team,
            start_date=transfer_date,
            end_date=None
        )
    
    def mark_as_injured(self, injury_details: str) -> None:
        """
        Mark the player as injured.
        
        Args:
            injury_details: Description of the injury
        """
        self.is_injured = True
        self.injury_details = injury_details
        self.save(update_fields=['is_injured', 'injury_details', 'updated_at'])
    
    def mark_as_healthy(self) -> None:
        """Mark the player as healthy (not injured)."""
        self.is_injured = False
        self.injury_details = ''
        self.save(update_fields=['is_injured', 'injury_details', 'updated_at'])
    
    def deactivate(self) -> None:
        """Deactivate the player (e.g., retired, waived)."""
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])
    
    def activate(self) -> None:
        """Activate the player."""
        self.is_active = True
        self.save(update_fields=['is_active', 'updated_at'])


class PlayerTeamHistory(models.Model):
    """
    Tracks a player's team history over time.
    
    This model records the teams a player has belonged to, including:
    - Which team they played for
    - When they joined and left
    - Any additional notes about the transfer
    
    Related models:
    - Player: The player whose history is being tracked
    - teams.Team: The team the player belonged to
    """
    player = models.ForeignKey(
        Player, 
        on_delete=models.CASCADE,
        help_text="Player whose team history is being tracked"
    )
    team = models.ForeignKey(
        'teams.Team', 
        on_delete=models.CASCADE,
        help_text="Team the player belonged to"
    )
    start_date = models.DateTimeField(
        help_text="When the player joined this team"
    )
    end_date = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When the player left this team"
    )
    transfer_notes = models.TextField(
        blank=True,
        help_text="Notes about the transfer (e.g., trade details, free agency)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Player Team History"
        verbose_name_plural = "Player Team Histories"
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['player', '-start_date']),
            models.Index(fields=['team', '-start_date']),
        ]
    
    def __str__(self) -> str:
        """Return a string representation of the team history entry."""
        return f"{self.player.user.get_full_name()} - {self.team.name} ({self.start_date.year})"
    
    @property
    def is_current(self) -> bool:
        """
        Check if this is the player's current team.
        
        Returns:
            bool: True if this is the player's current team
        """
        return self.end_date is None
