from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from typing import Optional, Any, Dict

class CustomUserManager(BaseUserManager):
    """
    Custom manager for the CustomUser model that handles email-based authentication.
    
    This manager provides methods to create regular users and superusers with email 
    as the unique identifier instead of username.
    """
    def create_user(self, email: str, password: Optional[str] = None, **extra_fields) -> 'CustomUser':
        """
        Create and save a regular user with the given email and password.
        
        Args:
            email: The user's email address (used as the login identifier)
            password: The user's password (option    def create_superuser(self, email: str, password: Optional[str] = None, **extra_fields) -> 'CustomUser':
        """
        Create and save a superuser with the given email and password.
        
        Args:
            email: The superuser's email address (used as the login identifier)
            password: The superuser's password (optional)
            **extra_fields: Additional fields to be set on the user instance
            
        Returns:
            The created superuser instance
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 'ADMIN')
        return self.create_user(email, password, **extra_fields)
class CustomUser(AbstractUser):
    """
    Custom user model that uses email for authentication instead of username.
    
    This model extends Django's AbstractUser to provide:
    - Email-based authentication instead of username
    - User type differentiation (admin, player, viewer)
    - Required first and last name fields
    
    Related models:
    - ViewerProfile: For viewer type users
    - players.Player: For player type users
    """
    USER_TYPES = (
        ('ADMIN', 'Admin'),
        ('PLAYER', 'Player'),
        ('VIEWER', 'Viewer'),
    )
    
    # Remove username field and use email instead
    username = None
    email = models.EmailField('email address', unique=True, db_index=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='VIEWER', db_index=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    def __str__(self):
        return self.email
        
    def get_full_name(self):
        """
        Return the user's full name.
        """
        return f"{self.first_name} {self.last_name}"
    
    def is_viewer(self):
        """
        Check if the user is a viewer.
        """
        return self.user_type == 'VIEWER'
    
    def is_player(self):
        """
        Check if the user is a player.
        """
        return self.user_type == 'PLAYER'
class ViewerProfile(models.Model):
    """
    Profile model for users of type 'VIEWER'.
    
    This model extends the CustomUser model with viewer-specific fields:
    - Subscription information
    - Subscription status tracking
    
    A viewer can purchase subscriptions, access streams, and buy tickets.
    """
    SUBSCRIPTION_TYPES = (
        ('NONE', 'No Subscription'),
        ('BASIC', 'Basic'),
        ('PREMIUM', 'Premium'),
    )
    
    user = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='viewer_profile'
    )
    subscription_type = models.CharField(
        max_length=10, 
        choices=SUBSCRIPTION_TYPES, 
        default='NONE',
        db_index=True
    )
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Viewer Profile"
        verbose_name_plural = "Viewer Profiles"
    def __str__(self):
        """Return a string representation of the viewer profile."""
        return f"Profile: {self.user.get_full_name()}"
    
    def is_subscription_active(self):
        """
        Check if the viewer's subscription is currently active.
        
        Returns:
            bool: True if subscription is active, False otherwise
        """
        if not self.subscription_end_date:
            return False
        return self.subscription_end_date > timezone.now()
    
    def get_subscription_days_remaining(self):
        """
        Calculate the number of days remaining in the current subscription.
        
        Returns:
            int: Number of days remaining, or 0 if subscription is inactive
        """
        if not self.is_subscription_active():
            return 0
        
        delta = self.subscription_end_date - timezone.now()
        return max(0, delta.days)
class Payment(models.Model):
    """
    Model to track all payment transactions in the system.
    
    This model handles different types of payments:
    - Ticket purchases
    - Stream access purchases
    - Subscription purchases
    
    It stores payment information, processing details, and status.
    """
    PAYMENT_TYPES = (
        ('TICKET', 'Match Ticket'),
        ('STREAM', 'Stream Access'),
        ('SUBSCRIPTION', 'Subscription'),
    )
    
    PAYMENT_STATUS = (
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    )
    
    user = models.ForeignKey(
        'accounts.CustomUser', 
        on_delete=models.CASCADE,
        related_name='payments'
    )
    payment_type = models.CharField(
        max_length=12, 
        choices=PAYMENT_TYPES,
        db_index=True
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    phone_number = models.CharField(max_length=15)
    merchant_request_id = models.CharField(max_length=100)
    checkout_request_id = models.CharField(max_length=100)
    reference_code = models.CharField(max_length=100, unique=True, db_index=True)
    status = models.CharField(
        max_length=10, 
        choices=PAYMENT_STATUS, 
        default='PENDING',
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['payment_type', 'status']),
        ]
    def __str__(self):
        """Return a string representation of the payment."""
        return f"{self.reference_code} - {self.payment_type}"
    
    def mark_as_completed(self):
        """
        Mark the payment as completed and update the timestamp.
        """
        self.status = 'COMPLETED'
        self.updated_at = timezone.now()
        self.save()
    
    def mark_as_failed(self):
        """
        Mark the payment as failed and update the timestamp.
        """
        self.status = 'FAILED'
        self.updated_at = timezone.now()
        self.save()
    
    def is_completed(self):
        """
        Check if the payment is completed.
        
        Returns:
            bool: True if payment is completed, False otherwise
        """
        return self.status == 'COMPLETED'
