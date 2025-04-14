from django.db import models
import uuid
from django.utils import timezone
from datetime import timedelta, timezone

class StreamingPlan(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.IntegerField()
    description = models.TextField()
    features = models.JSONField()
    is_active = models.BooleanField(default=True)

class GameStream(models.Model):
    STREAM_STATUS = (
        ('SCHEDULED', 'Scheduled'),
        ('LIVE', 'Live'),
        ('ENDED', 'Ended'),
        ('ARCHIVED', 'Archived'),
    )

    match = models.OneToOneField('games.Game', on_delete=models.CASCADE)
    stream_url = models.URLField()
    stream_key = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=STREAM_STATUS)
    is_premium = models.BooleanField(default=True)
    viewer_count = models.IntegerField(default=0)
    recording_url = models.URLField(blank=True, null=True)

class ViewerStreamAccess(models.Model):
    viewer = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE)
    game_stream = models.ForeignKey(GameStream, on_delete=models.CASCADE)
    access_granted = models.DateTimeField(auto_now_add=True)
    payment_id = models.CharField(max_length=100)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)

class StreamKey(models.Model):
    key = models.UUIDField(default=uuid.uuid4, unique=True)
    match = models.OneToOneField('games.Match', on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class StreamAccess(models.Model):
    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE)
    match = models.ForeignKey('games.Match', on_delete=models.CASCADE)
    access_key = models.UUIDField(default=uuid.uuid4, unique=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_valid(self):
        return self.expires_at > timezone.now()

class ViewershipStats(models.Model):
    match = models.ForeignKey('games.Match', on_delete=models.CASCADE)
    viewer_count = models.IntegerField(default=0)
    peak_viewers = models.IntegerField(default=0)
    total_watch_time = models.DurationField(default=timedelta())
    timestamp = models.DateTimeField(auto_now_add=True)

class ViewerSession(models.Model):
    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE)
    match = models.ForeignKey('games.Match', on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True)
    duration = models.DurationField(null=True)
    device_info = models.JSONField(default=dict)