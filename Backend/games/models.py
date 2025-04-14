from django.db import models

# Create your models here.

class Game(models.Model):
    MATCH_STATUS = [
        ('SCHEDULED', 'Scheduled'),
        ('LIVE', 'Live'),
        ('FINISHED', 'Finished'),
        ('POSTPONED', 'Postponed'),
    ]
    
    home_team = models.ForeignKey('teams.Team', on_delete=models.CASCADE, related_name='home_matches')
    away_team = models.ForeignKey('teams.Team', on_delete=models.CASCADE, related_name='away_matches')
    league = models.ForeignKey('teams.League', on_delete=models.CASCADE, related_name='matches')
    date_time = models.DateTimeField()
    venue = models.CharField(max_length=200)
    status = models.CharField(max_length=10, choices=MATCH_STATUS, default='SCHEDULED')
    home_score = models.IntegerField(null=True, blank=True)
    away_score = models.IntegerField(null=True, blank=True)
    stream_url = models.URLField(blank=True)
    ticket_price = models.DecimalField(max_digits=10, decimal_places=2)
    streaming_price = models.DecimalField(max_digits=10, decimal_places=2)
    available_tickets = models.IntegerField()
    is_playoff = models.BooleanField(default=False)
    is_playoff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_time']

    def __str__(self):
        return f"{self.home_team} vs {self.away_team} - {self.date_time.date()}"


class Ticket(models.Model):
    match = models.ForeignKey(Game, on_delete=models.CASCADE)
    viewer = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE)
    purchase_date = models.DateTimeField(auto_now_add=True)
    ticket_code = models.CharField(max_length=20, unique=True)
    is_used = models.BooleanField(default=False)
    payment_id = models.CharField(max_length=100)

class MatchStats(models.Model):
    match = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='stats')
    player = models.ForeignKey('players.Player', on_delete=models.CASCADE)
    points = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)
    rebounds = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['match', 'player']