from django.contrib import admin
from .models import Notification, NotificationSubscription

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'notification_type', 'title', 'created_at', 'is_read']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__email', 'title', 'message']
    readonly_fields = ['created_at']

@admin.register(NotificationSubscription)
class NotificationSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'device_type', 'is_active', 'created_at']
    list_filter = ['device_type', 'is_active', 'created_at']
    search_fields = ['user__email', 'device_token']
    readonly_fields = ['created_at', 'updated_at']
