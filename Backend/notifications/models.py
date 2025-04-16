from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid

class NotificationType(models.TextChoices):
    GAME_UPDATES = 'GAME_UPDATES', _('Game Updates')
    TEAM_NEWS = 'TEAM_NEWS', _('Team News')
    SCORES = 'SCORES', _('Scores')
    PLAYER_STATS = 'PLAYER_STATS', _('Player Stats')
    TICKET_UPDATES = 'TICKET_UPDATES', _('Ticket Updates')
    SYSTEM = 'SYSTEM', _('System Notifications')

class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    notification_type = models.CharField(
        max_length=20, 
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['user', 'notification_type'])
        ]
    
    def __str__(self):
        return f"{self.notification_type} - {self.title} - {self.user}"
    
    def mark_as_read(self):
        self.is_read = True
        self.save(update_fields=['is_read'])
    
    @classmethod
    def create_and_push(cls, user, notification_type, title, message, data=None):
        notification = cls.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            data=data
        )
        
        # Import here to avoid circular imports
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        
        # Push to user's notification group
        async_to_sync(channel_layer.group_send)(
            f"notifications_{user.id}",
            {
                "type": "notification.message",
                "message": {
                    "id": str(notification.id),
                    "notification_type": notification.notification_type,
                    "title": notification.title,
                    "message": notification.message,
                    "data": notification.data,
                    "created_at": notification.created_at.isoformat(),
                }
            }
        )
        
        return notification

class NotificationSubscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='notification_subscriptions'
    )
    notification_types = models.JSONField(default=list)
    device_token = models.CharField(max_length=255)
    device_type = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'device_token']
    
    def __str__(self):
        return f"Subscription - {self.user} - {self.device_type}"
