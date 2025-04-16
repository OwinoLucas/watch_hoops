from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction

from .models import Ticket, TicketPurchase, TicketType, TicketStatus
from .serializers import TicketSerializer, TicketPurchaseSerializer

class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Ticket.objects.filter(user=self.request.user)
        
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        game = self.request.query_params.get('game', None)
        if game:
            queryset = queryset.filter(game=game)
            
        return queryset
    
    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        ticket = self.get_object()
        
        if ticket.status != TicketStatus.ACTIVE:
            return Response(
                {"detail": f"Ticket is {ticket.status}"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if ticket.game.date_time > timezone.now():
            return Response(
                {"detail": "Game has not started yet"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        ticket.status = TicketStatus.USED
        ticket.validation_date = timezone.now()
        ticket.save()
        
        return Response({"status": "Ticket validated successfully"})

class TicketPurchaseViewSet(viewsets.ModelViewSet):
    serializer_class = TicketPurchaseSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return TicketPurchase.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        with transaction.atomic():
            purchase = serializer.save(
                user=self.request.user,
                total_price=self.calculate_total_price(
                    serializer.validated_data['game'],
                    serializer.validated_data['ticket_type'],
                    serializer.validated_data['quantity']
                )
            )
            
            # Create individual tickets
            for _ in range(purchase.quantity):
                Ticket.objects.create(
                    user=self.request.user,
                    game=purchase.game,
                    ticket_type=purchase.ticket_type,
                    price=purchase.total_price / purchase.quantity,
                    status=TicketStatus.ACTIVE
                )
            
            purchase.payment_status = 'COMPLETED'
            purchase.save()
            
            return purchase
    
    def calculate_total_price(self, game, ticket_type, quantity):
        base_price = game.ticket_price
        
        if ticket_type == TicketType.VIP:
            base_price *= 2
        elif ticket_type == TicketType.COURTSIDE:
            base_price *= 4
            
        return base_price * quantity
