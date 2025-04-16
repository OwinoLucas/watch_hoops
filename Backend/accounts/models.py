from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from typing import Optional


class CustomUserManager(BaseUserManager):
    """
    Custom manager for the CustomUser model that handles email-based authentication.
    """

    def create_user(self, email: str, password: Optional[str] = None, **extra_fields) -> 'CustomUser':
        """
        Create and save a regular user with the given email and password.

        Args:
            email (str): The user's email address (used as the login identifier)
            password (str, optional): The user's password
            **extra_fields: Additional fields to be set on the user instance

        Returns:
            CustomUser: The created user instance
        """
        if not email:
            raise ValueError('The Email field must be set')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: Optional[str] = None, **extra_fields) -> 'CustomUser':
        """
        Create and save a superuser with the given email and password.

        Args:
            email (str): The superuser's email address
            password (str, optional): The superuser's password
            **extra_fields: Additional fields to be set on the superuser instance

        Returns:
            CustomUser: The created superuser instance
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 'ADMIN')

        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser must have is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """
    Custom user model that uses email for authentication instead of username.
    """
    USER_TYPES = (
        ('ADMIN', 'Admin'),
        ('PLAYER', 'Player'),
        ('VIEWER', 'Viewer'),
    )

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
        return f"{self.first_name} {self.last_name}"

    def is_viewer(self):
        return self.user_type == 'VIEWER'

    def is_player(self):
        return self.user_type == 'PLAYER'


class ViewerProfile(models.Model):
    """
    Profile model for users of type 'VIEWER'.
    """
    SUBSCRIPTION_TYPES = (
        ('NONE', 'No Subscription'),
        ('BASIC', 'Basic'),
        ('PREMIUM', 'Premium'),
    )

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='viewer_profile')
    subscription_type = models.CharField(max_length=10, choices=SUBSCRIPTION_TYPES, default='NONE', db_index=True)
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Viewer Profile"
        verbose_name_plural = "Viewer Profiles"

    def __str__(self):
        return f"Profile: {self.user.get_full_name()}"

    def is_subscription_active(self):
        if not self.subscription_end_date:
            return False
        return self.subscription_end_date > timezone.now()

    def get_subscription_days_remaining(self):
        if not self.is_subscription_active():
            return 0
        delta = self.subscription_end_date - timezone.now()
        return max(0, delta.days)


class Payment(models.Model):
    """
    Model to track all payment transactions in the system.
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

    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='payments')
    payment_type = models.CharField(max_length=12, choices=PAYMENT_TYPES, db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    phone_number = models.CharField(max_length=15)
    merchant_request_id = models.CharField(max_length=100)
    checkout_request_id = models.CharField(max_length=100)
    reference_code = models.CharField(max_length=100, unique=True, db_index=True)
    status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='PENDING', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['payment_type', 'status']),
        ]

    def __str__(self):
        return f"{self.reference_code} - {self.payment_type}"

    def mark_as_completed(self):
        self.status = 'COMPLETED'
        self.updated_at = timezone.now()
        self.save()

    def mark_as_failed(self):
        self.status = 'FAILED'
        self.updated_at = timezone.now()
        self.save()

    def is_completed(self):
        return self.status == 'COMPLETED'
