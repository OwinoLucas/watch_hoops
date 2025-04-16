from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Notification, NotificationSubscription
from .serializers import NotificationSerializer, NotificationSubscriptionSerializer

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True)
        return Response({'status': 'success'})
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.mark_as_read()
        return Response({'status': 'success'})

class SubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return NotificationSubscription.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        subscription = self.get_object()
        subscription.is_active = True
        subscription.save()
        return Response({'status': 'success'})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        subscription = self.get_object()
        subscription.is_active = False
        subscription.save()
        return Response({'status': 'success'})
