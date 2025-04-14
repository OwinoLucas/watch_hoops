from django.db import models

# Create your models here.

class League(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    season_start = models.DateField()
    season_end = models.DateField()
    logo = models.ImageField(upload_to='leagues/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class Team(models.Model):
    name = models.CharField(max_length=100)
    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name='teams')
    logo = models.ImageField(upload_to='team_logos/')
    founded_year = models.IntegerField()
    home_venue = models.CharField(max_length=200)
    description = models.TextField()
    website = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name