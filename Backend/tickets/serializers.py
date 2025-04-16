from rest_framework import serializers
from django.utils import timezone
from .models import Ticket, TicketPurchase, TicketType, TicketStatus

class TicketSerializer(serializers.ModelSerializer):
    game_name = serializers.StringRelatedField(source='game', read_only=True)
    user_name = serializers.StringRelatedField(source='user', read_only=True)
    qr_code_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Ticket
        fields = [
            'id', 'user', 'user_name', 'game', 'game_name', 'ticket_type', 
            'status', 'price', 'purchase_date', 'validation_date', 
            'seat_info', 'qr_code_url'
        ]
        read_only_fields = ['id', 'user', 'status', 'purchase_date', 
                           'validation_date', 'qr_code_url']
    
    def get_qr_code_url(self, obj):
        if obj.qr_code:
            return obj.qr_code.url
        return None

class TicketPurchaseSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=True)
    game_name = serializers.StringRelatedField(source='game', read_only=True)
    
    class Meta:
        model = TicketPurchase
        fields = [
            'id', 'user', 'game', 'game_name', 'ticket_type', 'quantity',
            'total_price', 'purchase_date', 'tickets', 'payment_status'
        ]
        read_only_fields = ['id', 'total_price', 'purchase_date', 
                           'tickets', 'payment_status']
    
    def validate(self, data):
        game = data['game']
        quantity = data['quantity']
        
        if game.date_time < timezone.now():
            raise serializers.ValidationError("Cannot purchase tickets for past games")
            
        # Check ticket availability
        available_tickets = game.get_available_tickets(data['ticket_type'])
        if available_tickets < quantity:
            raise serializers.ValidationError(
                f"Only {available_tickets} {data['ticket_type']} tickets available"
            )
            
        return data
