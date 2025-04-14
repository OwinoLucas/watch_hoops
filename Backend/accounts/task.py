from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from datetime import timedelta
from django.utils import timezone

def send_game_reminder(user, match):
    context = {
        'user': user,
        'match': match,
    }
    
    html_message = render_to_string('emails/game_reminder.html', context)
    
    send_mail(
        subject=f'Reminder: {match.home_team} vs {match.away_team}',
        message='',
        html_message=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )

def send_subscription_expiry_reminder(user):
    days_left = (user.viewer_profile.subscription_end_date - timezone.now()).days
    
    context = {
        'user': user,
        'days_left': days_left,
    }
    
    html_message = render_to_string('emails/subscription_reminder.html', context)
    
    send_mail(
        subject='Your subscription is ending soon',
        message='',
        html_message=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )