from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import  StreamAccess
from games.models import Game
from django.utils import timezone
from datetime import timedelta, datetime

# Example: get the time 7 days ago from now
seven_days_ago = datetime.now() - timedelta(days=7)

print(seven_days_ago)


# @api_view(['POST'])
# def stream_auth(request):
#     """Authenticate RTMP stream publishing"""
#     stream_key = request.POST.get('name')
#     try:
#         stream = StreamKey.objects.get(key=stream_key, is_active=True)
#         return Response(status=status.HTTP_200_OK)
#     except StreamKey.DoesNotExist:
#         return Response(status=status.HTTP_403_FORBIDDEN)

class StreamAccessViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def create(self, request):
        match_id = request.data.get('match_id')
        match = get_object_or_404(Game, id=match_id)
        
        # Check if user has paid or has valid subscription
        if not request.user.viewer_profile.is_subscription_active():
            return Response(
                {"error": "Active subscription required"},
                status=status.HTTP_402_PAYMENT_REQUIRED
            )

        # Create or get stream access
        access, created = StreamAccess.objects.get_or_create(
            user=request.user,
            match=match,
            defaults={'expires_at': timezone.now() + timedelta(hours=4)}
        )

        return Response({
            "access_key": access.access_key,
            "expires_at": access.expires_at
        })
# Create your views here.
