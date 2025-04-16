from django.db import models
from django.utils import timezone
from typing import Optional, Tuple, Dict, Any

class Game(models.Model):
    """
    Represents a basketball game between two teams.
    
    This model stores all game details including:
    - Team matchups (home and away teams)
    - Game scheduling and venue information
    - Game status (scheduled, live, finished, postponed)
    - Scores
    - Ticket and streaming information
    
    Related models:
    - teams.Team: Home and away teams participating in the game
    - teams.League: The league this game belongs to
    - Ticket: Tickets purchased for this game
    - streaming.GameStream: Stream for this game
    - MatchStats: Player statistics for this game
    """
    MATCH_STATUS = [
        ('SCHEDULED', 'Scheduled'),
        ('LIVE', 'Live'),
        ('FINISHED', 'Finished'),
        ('POSTPONED', 'Postponed'),
    ]
    
    home_team = models.ForeignKey(
        'teams.Team', 
        on_delete=models.CASCADE, 
        related_name='home_matches',
        help_text="The team hosting the game"
    )
    away_team = models.ForeignKey(
        'teams.Team', 
        on_delete=models.CASCADE, 
        related_name='away_matches',
        help_text="The visiting team"
    )
    league = models.ForeignKey(
        'teams.League', 
        on_delete=models.CASCADE, 
        related_name='matches',
        help_text="The league this game belongs to"
    )
    date_time = models.DateTimeField(
        db_index=True,
        help_text="Scheduled date and time of the game"
    )
    venue = models.CharField(
        max_length=200,
        help_text="Location where the game will be played"
    )
    status = models.CharField(
        max_length=10, 
        choices=MATCH_STATUS, 
        default='SCHEDULED',
        db_index=True,
        help_text="Current status of the game"
    )
    home_score = models.IntegerField(
        null=True, 
        blank=True    class Meta:
        ordering = ['-date_time']
        indexes = [
            models.Index(fields=['status', 'date_time']),
            models.Index(fields=['league', 'status']),
            models.Index(fields=['home_team', 'away_team']),
        ]
        verbose_name = "Game"
        verbose_name_plural = "Games"
    
    def __str__(self) -> str:
        """Return a string representation of the game."""
        return f"{self.home_team} vs {self.away_team} - {self.date_time.date()}"
    
    @property
    def is_live(self) -> bool:
        """Check if the game is currently live."""
        return self.status == 'LIVE'
    
    @property
    def is_finished(self) -> bool:
        """Check if the game has finished."""
        return self.status == 'FINISHED'
    
    @property
    def score_display(self) -> str:
        """Get a formatted display of the current score."""
        if self.home_score is None or self.away_score is None:
            return "Not started"
        return f"{self.home_score} - {self.away_score}"
    
    def update_score(self, home_score: int, away_score: int) -> None:
        """
        Update the game score.
        
        Args:
            home_score: The new score for the home team
            away_score: The new score for the away team
        """
        self.home_score = home_score
        self.away_score = away_score
        self.save(update_fields=['home_score', 'away_score', 'updated_at'])
    
    def start_game(self) -> None:
        """Mark the game as live."""
        self.status = 'LIVE'
        self.save(update_fields=['status', 'updated_at'])
    
    def end_game(self) -> None:
        """Mark the game as finished."""
        self.status = 'FINISHED'
        self.save(update_fields=['status', 'updated_at'])
    
    def postpone_game(self) -> None:
        """Mark the game as postponed."""
        self.status = 'POSTPONED'
        self.save(update_fields=['status', 'updated_at'])
    
    def has_available_tickets(self) -> bool:
        """Check if there are tickets available for purchase."""
        return self.available_tickets > 0
    
    def decrease_available_tickets(self, count: int = 1) -> None:
        """
        Decrease the number of available tickets.
        
        Args:
            count: Number of tickets to decrease (default: 1)
        """
        if self.available_tickets >= count:
            self.available_tickets -= count
            self.save(update_fields=['available_tickets', 'updated_at'])
class Ticket(models.Model):
    """
    Represents a purchased ticket for a game.
    
    This model tracks ticket purchases, usage status, and payment information.
    
    Related models:
    - Game: The game this ticket is for
    - accounts.CustomUser: The user who purchased the ticket
    """
    match = models.ForeignKey(
        Game, 
        on_delete=models.CASCADE,
        related_name='tickets',
        help_text="The game this ticket is for"
    )
    viewer = models.ForeignKey(
        'accounts.CustomUser', 
        on_delete=models.CASCADE,
        related_name='tickets',
        help_text="The user who purchased this ticket"
    )
    purchase_date = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When the ticket was purchased"
    )
    ticket_code = models.CharField(
        max_length=20, 
        unique=True, 
        db_index=True,
        help_text="Unique code to identify this ticket"
    )
    is_used = models.BooleanField(
        default=False,
        help_text="Whether the ticket has been used to enter the venue"
    )
    payment_id = models.CharField(
        max_length=100,
        help_text="ID of the payment transaction for this ticket"
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['viewer', 'match']),
            models.Index(fields=['match', 'is_used']),
        ]
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"
    
    def __str__(self) -> str:
        """Return a string representation of the ticket."""
        return f"Ticket {self.ticket_code} for {self.match}"
    
    def mark_as_used(self) -> None:
        """Mark the ticket as used."""
        self.is_used = True
        self.save(update_fields=['is_used'])
    
    @property
    def is_valid(self) -> bool:
        """
        Check if the ticket is valid for use.
        
        A ticket is valid if:
        - It hasn't been used yet
        - The game hasn't finished
        """
        return not self.is_used and not self.match.is_finished
class MatchStats(models.Model):
    """
    Represents player statistics for a specific game.
    
    This model tracks individual player performance metrics for each game,
    such as points, assists, and rebounds.
    
    Related models:
    - Game: The game these statistics are for
    - players.Player: The player these statistics belong to
    """
    match = models.ForeignKey(
        Game, 
        on_delete=models.CASCADE, 
        related_name='stats',
        help_text="The game these statistics are for"
    )
    player = models.ForeignKey(
        'players.Player', 
        on_delete=models.CASCADE,
        related_name='match_stats',
        help_text="The player these statistics belong to"
    )
    points = models.IntegerField(
        default=0,
        help_text="Number of points scored"
    )
    assists = models.IntegerField(
        default=0,
        help_text="Number of assists"
    )
    rebounds = models.IntegerField(
        default=0,
        help_text="Number of rebounds"
    )
    steals = models.IntegerField(
        default=0,
        help_text="Number of steals"
    )
    blocks = models.IntegerField(
        default=0,
        help_text="Number of blocks"
    )
    turnovers = models.IntegerField(
        default=0,
        help_text="Number of turnovers"
    )
    minutes_played = models.IntegerField(
        default=0,
        help_text="Minutes played in the game"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['match', 'player']
        indexes = [
            models.Index(fields=['match']),
            models.Index(fields=['player']),
        ]
        verbose_name = "Match Statistics"
        verbose_name_plural = "Match Statistics"
    
    def __str__(self) -> str:
        """Return a string representation of the match statistics."""
        return f"{self.player} stats for {self.match}"
    
    @property
    def efficiency(self) -> float:
        """
        Calculate player efficiency rating for this game.
        
        Returns:
            float: Player efficiency rating
        """
        return (self.points + self.rebounds + self.assists + self.steals + self.blocks) - self.turnovers
