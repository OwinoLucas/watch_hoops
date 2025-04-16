from django.db import models
from django.utils import timezone
from games.models import Game
from tickets.models import Ticket

class SalesReport(models.Model):
    date = models.DateField(default=timezone.now)
    total_tickets_sold = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2)
    avg_ticket_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Sales Report - {self.date}"

class AttendanceReport(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='attendance_reports')
    total_attendance = models.IntegerField(default=0)
    attendance_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    ticket_types = models.JSONField(default=dict)  # Store counts by ticket type
    
    class Meta:
        ordering = ['-game__date_time']

    def __str__(self):
        return f"Attendance Report - {self.game}"

class RevenueReport(models.Model):
    start_date = models.DateField()
    end_date = models.DateField()
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2)
    ticket_revenue = models.DecimalField(max_digits=10, decimal_places=2)
    streaming_revenue = models.DecimalField(max_digits=10, decimal_places=2)
    report_type = models.CharField(max_length=20, choices=[
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
        ('YEARLY', 'Yearly')
    ])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.report_type} Revenue Report ({self.start_date} to {self.end_date})"
