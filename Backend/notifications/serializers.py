from rest_framework import serializers
from .models import Notification, NotificationSubscription, NotificationType

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'title', 'message', 
            'data', 'created_at', 'is_read'
        ]
        read_only_fields = ['id', 'notification_type', 'created_at']

class NotificationSubscriptionSerializer(serializers.ModelSerializer):
    notification_types = serializers.ListField(
        child=serializers.ChoiceField(choices=NotificationType.choices),
        required=True,
        help_text="List of notification types to subscribe to"
    )
    
    class Meta:
        model = NotificationSubscription
        fields = [
            'id', 'notification_types', 'device_token', 
            'device_type', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def validate_notification_types(self, value):
        valid_types = [choice[0] for choice in NotificationType.choices]
        for notification_type in value:
            if notification_type not in valid_types:
                raise serializers.ValidationError(
                    f"Invalid notification type: {notification_type}"
                )
        return value
