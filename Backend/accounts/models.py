from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 'ADMIN')
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    USER_TYPES = (
        ('ADMIN', 'Admin'),
        ('PLAYER', 'Player'),
        ('VIEWER', 'Viewer'),  # Changed FAN to VIEWER
    )

    username = None
    email = models.EmailField('email address', unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='VIEWER')
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email

class ViewerProfile(models.Model):
    SUBSCRIPTION_TYPES = (
        ('NONE', 'No Subscription'),
        ('BASIC', 'Basic'),
        ('PREMIUM', 'Premium'),
    )

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='viewer_profile')
    subscription_type = models.CharField(max_length=10, choices=SUBSCRIPTION_TYPES, default='NONE')
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_subscription_active(self):
        if not self.subscription_end_date:
            return False
        return self.subscription_end_date > timezone.now()

class Payment(models.Model):
    PAYMENT_TYPES = (
        ('TICKET', 'Match Ticket'),
        ('STREAM', 'Stream Access'),
        ('SUBSCRIPTION', 'Subscription'),
    )
    
    PAYMENT_STATUS = (
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    )

    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE)
    payment_type = models.CharField(max_length=12, choices=PAYMENT_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    phone_number = models.CharField(max_length=15)
    merchant_request_id = models.CharField(max_length=100)
    checkout_request_id = models.CharField(max_length=100)
    reference_code = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.reference_code} - {self.payment_type}"