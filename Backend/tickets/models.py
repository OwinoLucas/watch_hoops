from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image

class TicketType(models.TextChoices):
    STANDARD = 'STANDARD', _('Standard')
    VIP = 'VIP', _('VIP')
    COURTSIDE = 'COURTSIDE', _('Courtside')

class TicketStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', _('Active')
    USED = 'USED', _('Used')
    EXPIRED = 'EXPIRED', _('Expired')
    CANCELLED = 'CANCELLED', _('Cancelled')

class Ticket(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='purchased_tickets'  # Changed from 'tickets'
    )
    game = models.ForeignKey(
        'games.Game', 
        on_delete=models.CASCADE, 
        related_name='game_tickets'  # Changed from 'tickets'
    )
    ticket_type = models.CharField(max_length=20, choices=TicketType.choices)
    status = models.CharField(max_length=20, choices=TicketStatus.choices, default=TicketStatus.ACTIVE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_date = models.DateTimeField(auto_now_add=True)
    validation_date = models.DateTimeField(null=True, blank=True)
    seat_info = models.JSONField(null=True, blank=True)
    qr_code = models.ImageField(upload_to='tickets/qr_codes/', null=True, blank=True)

    class Meta:
        ordering = ['-purchase_date']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['game', 'ticket_type']),
        ]

    def __str__(self):
        return f"{self.ticket_type} Ticket - {self.game} - {self.user}"

    def save(self, *args, **kwargs):
        if not self.qr_code:
            self.generate_qr_code()
        super().save(*args, **kwargs)

    def generate_qr_code(self):
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(str(self.id))
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        filename = f'ticket_qr_{self.id}.png'
        self.qr_code.save(filename, File(buffer), save=False)

class TicketPurchase(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='ticket_purchases'
    )
    game = models.ForeignKey(
        'games.Game', 
        on_delete=models.CASCADE, 
        related_name='ticket_sales'  # Changed from 'ticket_purchases'
    )
    ticket_type = models.CharField(max_length=20, choices=TicketType.choices)
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_date = models.DateTimeField(auto_now_add=True)
    payment_status = models.CharField(max_length=20, default='PENDING')

    class Meta:
        ordering = ['-purchase_date']

    def __str__(self):
        return f"{self.quantity} {self.ticket_type} tickets - {self.game}"
