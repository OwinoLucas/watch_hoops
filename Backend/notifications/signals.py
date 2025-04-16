from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from games.models import Game
from tickets.models import Ticket
from .models import Notification, NotificationType

User = get_user_model()

@receiver(post_save, sender=Game)
def game_notification(sender, instance, created, **kwargs):
    """
    Send notifications for game updates
    """
    from .models import NotificationSubscription
    
    if created:
        # Notify users subscribed to game updates
        subscriptions = NotificationSubscription.objects.filter(
            notification_types__contains=['GAME_UPDATES'],
            is_active=True
        )
        
        for subscription in subscriptions:
            Notification.create_and_push(
                user=subscription.user,
                notification_type=NotificationType.GAME_UPDATES,
                title="New Game Scheduled",
                message=f"{instance.home_team} vs {instance.away_team} on {instance.date_time.strftime('%Y-%m-%d %H:%M')}",
                data={
                    'game_id': instance.id,
                    'home_team': instance.home_team.id,
                    'away_team': instance.away_team.id,
                    'date': instance.date_time.isoformat()
                }
            )
    
    elif instance.is_live and instance.tracker.has_changed('is_live'):
        # Game has started - notify ticket holders and subscribers
        ticket_holders = User.objects.filter(
            tickets__game=instance,
            tickets__status='ACTIVE'
        ).distinct()
        
        for user in ticket_holders:
            Notification.create_and_push(
                user=user,
                notification_type=NotificationType.GAME_UPDATES,
                title="Game Starting Soon",
                message=f"{instance.home_team} vs {instance.away_team} is starting now!",
                data={
                    'game_id': instance.id,
                    'status': 'LIVE'
                }
            )

@receiver(post_save, sender=Ticket)
def ticket_notification(sender, instance, created, **kwargs):
    """
    Send notifications for ticket updates
    """
    if created:
        Notification.create_and_push(
            user=instance.user,
            notification_type=NotificationType.TICKET_UPDATES,
            title="Ticket Purchase Confirmed",
            message=f"Your ticket for {instance.game} has been confirmed.",
            data={
                'ticket_id': str(instance.id),
                'game_id': instance.game.id,
                'ticket_type': instance.ticket_type
            }
        )
    
    elif instance.status == 'USED':
        Notification.create_and_push(
            user=instance.user,
            notification_type=NotificationType.TICKET_UPDATES,
            title="Ticket Used",
            message=f"Your ticket for {instance.game} has been validated and marked as used.",
            data={
                'ticket_id': str(instance.id),
                'game_id': instance.game.id,
                'status': 'USED'
            }
        )
