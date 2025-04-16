import time
import json
import traceback
import logging
from django.utils import timezone
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

from .models import RequestLog, ErrorLog, PerformanceMetric

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log API requests for monitoring and analytics
    """
    
    def __init__(self, get_response=None):
        self.get_response = get_response
        # Skip logging for these paths
        self.IGNORED_PATHS = getattr(settings, 'MONITORING_IGNORED_PATHS', [
            '/admin/', 
            '/static/', 
            '/media/',
            '/health/basic',  # Don't log basic health checks to avoid clutter
        ])
    
    def should_log_request(self, request):
        """Determine if this request should be logged"""
        # Skip if path is in ignored paths
        path = request.path
        for ignored_path in self.IGNORED_PATHS:
            if path.startswith(ignored_path):
                return False
                
        # Skip internal requests
        is_internal = request.META.get('HTTP_X_INTERNAL', False)
        if is_internal:
            return False
            
        # Log all requests to API endpoints
        if path.startswith('/api/'):
            return True
            
        # Default to not logging
        return False
    
    def process_request(self, request):
        """Store start time for performance tracking"""
        if not self.should_log_request(request):
            return None
            
        request.start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """Log the request and response after processing"""
        if not self.should_log_request(request) or not hasattr(request, 'start_time'):
            return response
            
        # Calculate response time
        response_time = time.time() - request.start_time
        response_time_ms = int(response_time * 1000)
        
        # Extract useful request data
        user = getattr(request, 'user', None)
        user_id = user.id if user and user.is_authenticated else None
        
        ip_address = request.META.get('REMOTE_ADDR', None)
        user_agent = request.META.get('HTTP_USER_AGENT', None)
        
        # Clean paths from common query params for better grouping
        path = request.path
        
        # Limit request data stored for privacy and security
        try:
            request_data = None
            
            # Only store request data for non-GET methods
            if request.method not in ['GET', 'HEAD']:
                # Get request data from body or POST
                if hasattr(request, 'body') and request.body:
                    # Try to parse JSON, fall back to raw POST data
                    try:
                        request_data = json.loads(request.body.decode('utf-8'))
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        # If not JSON, get POST data
                        request_data = dict(request.POST.items())
                        
                # Remove sensitive fields
                if request_data:
                    sensitive_fields = ['password', 'token', 'secret', 'credit_card', 'card_number']
                    for field in sensitive_fields:
                        if field in request_data:
                            request_data[field] = '***REDACTED***'
        except Exception as e:
            logger.warning(f"Error extracting request data: {str(e)}")
            request_data = None
        
        try:
            # Log the request
            RequestLog.objects.create(
                path=path,
                method=request.method,
                status_code=response.status_code,
                response_time_ms=response_time_ms,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                request_data=request_data
            )
            
            # Store performance metric for slower requests only (configurable threshold)
            threshold_ms = getattr(settings, 'MONITORING_SLOW_REQUEST_THRESHOLD_MS', 500)
            if response_time_ms > threshold_ms:
                # Create performance metric
                PerformanceMetric.objects.create(
                    metric_type='RESPONSE_TIME',
                    metric_name=f"{request.method} {path}",
                    value=response_time_ms,
                    unit='ms'
                )
                
                # Log slow request
                logger.warning(f"Slow request: {request.method} {path} - {response_time_ms}ms")
        except Exception as e:
            logger.error(f"Error logging request: {str(e)}")
        
        return response


class ErrorLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log API errors for troubleshooting and monitoring
    """
    
    def process_exception(self, request, exception):
        """Log the exception"""
        try:
            # Get error details
            error_type = exception.__class__.__name__
            error_message = str(exception)
            stack_trace = traceback.format_exc()
            
            # Extract user data
            user = getattr(request, 'user', None)
            user_id = user.id if user and user.is_authenticated else None
            
            # Extract request data
            ip_address = request.META.get('REMOTE_ADDR', None)
            user_agent = request.META.get('HTTP_USER_AGENT', None)
            
            # Extract request body data
            try:
                if hasattr(request, 'body') and request.body:
                    # Try to parse JSON, fall back to raw POST data
                    try:
                        request_data = json.loads(request.body.decode('utf-8'))
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        request_data = dict(request.POST.items())
                else:
                    request_data = None
                    
                # Remove sensitive fields
                if request_data:
                    sensitive_fields = ['password', 'token', 'secret', 'credit_card', 'card_number']
                    for field in sensitive_fields:
                        if field in request_data:
                            request_data[field] = '***REDACTED***'
            except Exception:
                request_data = None
            
            # Log the error
            ErrorLog.objects.create(
                path=request.path,
                method=request.method,
                error_type=error_type,
                error_message=error_message,
                stack_trace=stack_trace,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                request_data=request_data
            )
            
            # Also log to the standard logging system
            logger.error(
                f"Exception in {request.method} {request.path}: {error_type} - {error_message}",
                exc_info=True
            )
            
        except Exception as e:
            # Last resort error logging
            logger.error(f"Error in error logging middleware: {str(e)}")
        
        # Return None to allow standard exception handling
        return None


class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """
    Middleware to monitor system performance metrics
    """
    
    def __init__(self, get_response=None):
        self.get_response = get_response
        self.last_sample_time = time.time()
        self.sample_interval = getattr(settings, 'MONITORING_METRIC_SAMPLE_INTERVAL', 300)  # 5 minutes by default
    
    def process_request(self, request):
        """Periodically sample system metrics"""
        current_time = time.time()
        
        # Only sample metrics at the configured interval
        if current_time - self.last_sample_time > self.sample_interval:
            try:
                self.sample_system_metrics()
                self.last_sample_time = current_time
            except Exception as e:
                logger.error(f"Error sampling system metrics: {str(e)}")
        
        return None
    
    def sample_system_metrics(self):
        """Sample and record system metrics"""
        try:
            import psutil
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            PerformanceMetric.objects.create(
                metric_type='CPU',
                metric_name='cpu_usage',
                value=cpu_percent,
                unit='percent'
            )
            
            # Memory usage
            memory = psutil.virtual_memory()
            PerformanceMetric.objects.create(
                metric_type='MEMORY',
                metric_name='memory_usage',
                value=memory.percent,
                unit='percent'
            )
            
            # Disk usage
            disk = psutil.disk_usage('/')
            PerformanceMetric.objects.create(
                metric_type='DISK',
                metric_name='disk_usage',
                value=disk.percent,
                unit='percent'
            )
            
        except ImportError:
            logger.warning("psutil not installed, system metrics not available")
        except Exception as e:
            logger.error(f"Error sampling system metrics: {str(e)}")

