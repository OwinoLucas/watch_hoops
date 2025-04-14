from django.db import models
from django.conf import settings

# Create your models here.


class Player(models.Model):
    POSITIONS = [
        ('PG', 'Point Guard'),
        ('SG', 'Shooting Guard'),
        ('SF', 'Small Forward'),
        ('PF', 'Power Forward'),
        ('C', 'Center'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='player_profile')
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    team = models.ForeignKey('teams.Team', on_delete=models.CASCADE, related_name='players')
    jersey_number = models.IntegerField()
    position = models.CharField(max_length=2, choices=POSITIONS)
    height = models.DecimalField(max_digits=3, decimal_places=2)  # in meters
    weight = models.IntegerField()  # in kg
    date_of_birth = models.DateField()
    photo = models.ImageField(upload_to='player_photos/', null=True, blank=True)
    bio = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class PlayerStats(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='stats')
    season_year = models.IntegerField()
    games_played = models.IntegerField(default=0)
    points_per_game = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    assists_per_game = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    rebounds_per_game = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-season_year']
        unique_together = ['player', 'season_year']