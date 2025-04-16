from django.contrib import admin
from .models import Ticket, TicketPurchase

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'game', 'ticket_type', 'status', 'purchase_date']
    list_filter = ['status', 'ticket_type', 'purchase_date']
    search_fields = ['user__email', 'game__name']
    readonly_fields = ['qr_code']

@admin.register(TicketPurchase)
class TicketPurchaseAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'game', 'ticket_type', 'quantity', 'payment_status']
    list_filter = ['payment_status', 'ticket_type', 'purchase_date']
    search_fields = ['user__email', 'game__name']
