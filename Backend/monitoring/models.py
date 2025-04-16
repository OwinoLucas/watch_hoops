from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class RequestLog(models.Model):
    """
    Model to log API requests for monitoring and analytics
    """
    METHOD_CHOICES = (
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('PATCH', 'PATCH'),
        ('DELETE', 'DELETE'),
        ('HEAD', 'HEAD'),
        ('OPTIONS', 'OPTIONS'),
    )
    
    path = models.CharField(max_length=255)
    method = models.CharField(max_length=10, choices=METHOD_CHOICES)
    status_code = models.IntegerField()
    response_time_ms = models.IntegerField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    request_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['path']),
            models.Index(fields=['method']),
            models.Index(fields=['status_code']),
            models.Index(fields=['user']),
            models.Index(fields=['-created_at']),
        ]
        verbose_name = 'Request Log'
        verbose_name_plural = 'Request Logs'
    
    def __str__(self):
        return f"{self.method} {self.path} - {self.status_code}"


class ErrorLog(models.Model):
    """
    Model to log API errors for troubleshooting and monitoring
    """
    path = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    error_type = models.CharField(max_length=255)
    error_message = models.TextField()
    stack_trace = models.TextField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    request_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['path']),
            models.Index(fields=['error_type']),
            models.Index(fields=['-created_at']),
        ]
        verbose_name = 'Error Log'
        verbose_name_plural = 'Error Logs'
    
    def __str__(self):
        return f"{self.error_type}: {self.path}"


class PerformanceMetric(models.Model):
    """
    Model to store system performance metrics
    """
    METRIC_TYPES = (
        ('CPU', 'CPU Usage'),
        ('MEMORY', 'Memory Usage'),
        ('RESPONSE_TIME', 'API Response Time'),
        ('DATABASE', 'Database Performance'),
        ('CACHE', 'Cache Performance'),
        ('CUSTOM', 'Custom Metric'),
    )
    
    metric_type = models.CharField(max_length=20, choices=METRIC_TYPES)
    metric_name = models.CharField(max_length=100)
    value = models.FloatField()
    unit = models.CharField(max_length=20)
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        indexes = [
            models.Index(fields=['metric_type']),
            models.Index(fields=['metric_name']),
            models.Index(fields=['-timestamp']),
        ]
        verbose_name = 'Performance Metric'
        verbose_name_plural = 'Performance Metrics'
    
    def __str__(self):
        return f"{self.metric_name}: {self.value} {self.unit}"


class SystemStatus(models.Model):
    """
    Model to store system status and health check results
    """
    STATUS_CHOICES = (
        ('HEALTHY', 'Healthy'),
        ('DEGRADED', 'Degraded'),
        ('DOWN', 'Down'),
    )
    
    COMPONENT_TYPES = (
        ('API', 'API Server'),
        ('DATABASE', 'Database'),
        ('CACHE', 'Cache'),
        ('ELASTICSEARCH', 'Elasticsearch'),
        ('CELERY', 'Celery'),
        ('REDIS', 'Redis'),
        ('EXTERNAL', 'External Service'),
    )
    
    component = models.CharField(max_length=20, choices=COMPONENT_TYPES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    message = models.TextField(null=True, blank=True)
    last_checked = models.DateTimeField(auto_now=True)
    uptime_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    class Meta:
        verbose_name = 'System Status'
        verbose_name_plural = 'System Status'
    
    def __str__(self):
        return f"{self.component}: {self.status}"
