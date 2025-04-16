from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncMonth, TruncDay
from django.db.models import Sum, Count, Avg
from games.serializers import MatchSerializer as GameSerializer

from .models import SalesReport, AttendanceReport, RevenueReport
from .serializers import SalesReportSerializer, AttendanceReportSerializer, RevenueReportSerializer
from tickets.models import Ticket, TicketPurchase
from games.models import Game
from datetime import timezone, timedelta
# from games.serializers import GameSerializer

class ReportsViewSet(viewsets.ViewSet):
    
    @action(detail=False, methods=['get'])
    def ticket_sales(self, request):
        """Get ticket sales reports"""
        period = request.query_params.get('period', 'daily')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Base queryset
        queryset = TicketPurchase.objects.all()
        
        # Apply date filters
        if start_date:
            queryset = queryset.filter(purchase_date__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(purchase_date__date__lte=end_date)
            
        # Group by period
        if period == 'monthly':
            sales = queryset.annotate(
                month=TruncMonth('purchase_date')
            ).values('month').annotate(
                total_sales=Sum('total_price'),
                tickets_sold=Sum('quantity')
            ).order_by('month')
        else:  # daily
            sales = queryset.annotate(
                day=TruncDay('purchase_date')
            ).values('day').annotate(
                total_sales=Sum('total_price'),
                tickets_sold=Sum('quantity')
            ).order_by('day')
        
        return Response(sales)
    
    @action(detail=False, methods=['get'])
    def attendance(self, request):
        """Get game attendance reports"""
        game_id = request.query_params.get('game_id')
        
        if game_id:
            # Single game attendance
            game = Game.objects.get(id=game_id)
            tickets = Ticket.objects.filter(game=game)
            
            report = {
                'game': GameSerializer(game).data,
                'total_tickets': tickets.count(),
                'used_tickets': tickets.filter(status='USED').count(),
                'by_type': tickets.values('ticket_type').annotate(
                    count=Count('id')
                )
            }
        else:
            # Overall attendance stats
            recent_games = Game.objects.filter(
                is_finished=True
            ).order_by('-date_time')[:10]
            
            reports = []
            for game in recent_games:
                tickets = Ticket.objects.filter(game=game)
                reports.append({
                    'game': GameSerializer(game).data,
                    'total_tickets': tickets.count(),
                    'used_tickets': tickets.filter(status='USED').count(),
                })
        
        return Response(reports if not game_id else report)
    
    @action(detail=False, methods=['get'])
    def revenue(self, request):
        """Get revenue reports"""
        period = request.query_params.get('period', 'monthly')
        year = request.query_params.get('year', timezone.now().year)
        
        # Get ticket sales revenue
        ticket_sales = TicketPurchase.objects.filter(
            purchase_date__year=year
        )
        
        if period == 'monthly':
            revenue = ticket_sales.annotate(
                month=TruncMonth('purchase_date')
            ).values('month').annotate(
                total_revenue=Sum('total_price'),
                avg_ticket_price=Avg('total_price')
            ).order_by('month')
        elif period == 'quarterly':
            # Implement quarterly aggregation
            pass
        else:  # yearly
            revenue = ticket_sales.aggregate(
                total_revenue=Sum('total_price'),
                avg_ticket_price=Avg('total_price')
            )
        
        return Response(revenue)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get summary of all reports"""
        # Get today's date
        today = timezone.now().date()
        
        # Today's sales
        today_sales = TicketPurchase.objects.filter(
            purchase_date__date=today
        ).aggregate(
            total_sales=Sum('total_price'),
            tickets_sold=Sum('quantity')
        )
        
        # Monthly revenue
        current_month = TicketPurchase.objects.filter(
            purchase_date__month=today.month,
            purchase_date__year=today.year
        ).aggregate(
            total_revenue=Sum('total_price')
        )
        
        # Recent games attendance
        recent_games = Game.objects.filter(
            is_finished=True,
            date_time__date__gte=today - timedelta(days=30)
        )
        attendance = Ticket.objects.filter(
            game__in=recent_games,
            status='USED'
        ).count()
        
        return Response({
            'today_sales': today_sales,
            'monthly_revenue': current_month,
            'recent_attendance': attendance,
            'date': today.isoformat()
        })
