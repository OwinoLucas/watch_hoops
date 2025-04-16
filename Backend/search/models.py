from django.db import models


class SearchIndex(models.Model):
    """
    Model to track the search index status
    """
    OBJECT_TYPES = (
        ('player', 'Player'),
        ('team', 'Team'),
        ('game', 'Game'),
        ('news', 'News'),
    )
    
    object_type = models.CharField(max_length=20, choices=OBJECT_TYPES)
    object_id = models.PositiveIntegerField()
    indexed_at = models.DateTimeField(auto_now=True)
    is_indexed = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('object_type', 'object_id')
        indexes = [
            models.Index(fields=['object_type', 'is_indexed']),
        ]
        
    def __str__(self):
        return f"{self.object_type} - {self.object_id} - {'Indexed' if self.is_indexed else 'Not Indexed'}"


class SearchQuery(models.Model):
    """
    Model to track search queries for analytics
    """
    query = models.CharField(max_length=255)
    user = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    results_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['query']),
        ]
        
    def __str__(self):
        return f"{self.query} - {self.results_count} results"
