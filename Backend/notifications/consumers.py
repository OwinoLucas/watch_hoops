import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        
        # Reject connection if user is not authenticated
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Add user to their notification group
        self.user_group_name = f"notifications_{self.user.id}"
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send unread notifications count on connect
        count = await self.get_unread_count()
        await self.send(text_data=json.dumps({
            'type': 'unread_count',
            'count': count
        }))
    
    async def disconnect(self, close_code):
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'mark_read':
                notification_id = data.get('notification_id')
                success = await self.mark_notification_read(notification_id)
                
                if success:
                    count = await self.get_unread_count()
                    await self.send(text_data=json.dumps({
                        'type': 'unread_count',
                        'count': count
                    }))
            
            elif message_type == 'mark_all_read':
                await self.mark_all_notifications_read()
                await self.send(text_data=json.dumps({
                    'type': 'unread_count',
                    'count': 0
                }))
            
            elif message_type == 'get_unread':
                count = await self.get_unread_count()
                await self.send(text_data=json.dumps({
                    'type': 'unread_count',
                    'count': count
                }))
        
        except json.JSONDecodeError:
            pass
    
    async def notification_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': event['message']
        }))
    
    @database_sync_to_async
    def get_unread_count(self):
        from .models import Notification
        return Notification.objects.filter(
            user=self.user,
            is_read=False
        ).count()
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        from .models import Notification
        try:
            notification = Notification.objects.get(
                id=notification_id,
                user=self.user
            )
            notification.mark_as_read()
            return True
        except Notification.DoesNotExist:
            return False
    
    @database_sync_to_async
    def mark_all_notifications_read(self):
        from .models import Notification
        Notification.objects.filter(
            user=self.user,
            is_read=False
        ).update(is_read=True)
