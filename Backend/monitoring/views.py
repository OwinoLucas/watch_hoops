import psutil
import redis
import django
import sys
import os
import json
import datetime
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.db import connection
from django.utils import timezone
from django.db.models import Avg, Count, Sum, Min, Max, F
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from .models import (
    RequestLog,
    ErrorLog,
    PerformanceMetric,
    SystemStatus
)


class HealthCheckViewSet(viewsets.ViewSet):
    """
    ViewSet for system health and status checking
    """
    
    @action(detail=False, methods=['get'], permission_classes=[])
    def basic(self, request):
        """
        Basic health check - returns 200 if API is running
        This endpoint is public to allow for automated monitoring
        """
        return Response({
            "status": "healthy",
            "timestamp": timezone.now(),
            "api_version": getattr(settings, 'API_VERSION', 'unknown')
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def detailed(self, request):
        """
        Detailed health check - returns status of all system components
        Requires authentication
        """
        # Check database connection
        db_status = 'healthy'
        db_message = 'Connection OK'
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception as e:
            db_status = 'down'
            db_message = str(e)
        
        # Check Redis connection
        redis_status = 'healthy'
        redis_message = 'Connection OK'
        try:
            redis_client = redis.Redis.from_url(settings.CACHES['default']['LOCATION'])
            redis_client.ping()
        except Exception as e:
            redis_status = 'down'
            redis_message = str(e)
        
        # Check Elasticsearch connection
        es_status = 'healthy'
        es_message = 'Connection OK'
        try:
            from elasticsearch_dsl.connections import connections
            es = connections.get_connection()
            es.info()
        except Exception as e:
            es_status = 'down'
            es_message = str(e)
        
        # Get system info
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Update SystemStatus records
        components = [
            ('API', 'healthy', 'API server is running'),
            ('DATABASE', db_status, db_message),
            ('CACHE', redis_status, redis_message),
            ('ELASTICSEARCH', es_status, es_message)
        ]
        
        for component, status, message in components:
            SystemStatus.objects.update_or_create(
                component=component,
                defaults={
                    'status': status.upper(),
                    'message': message
                }
            )
        
        return Response({
            "status": "healthy" if all(s[1] == 'healthy' for s in components) else "degraded",
            "timestamp": timezone.now(),
            "api_version": getattr(settings, 'API_VERSION', 'unknown'),
            "components": {
                "api": {
                    "status": "healthy",
                    "uptime": time.time() - psutil.boot_time()
                },
                "database": {
                    "status": db_status,
                    "message": db_message
                },
                "cache": {
                    "status": redis_status,
                    "message": redis_message
                },
                "elasticsearch": {
                    "status": es_status,
                    "message": es_message
                }
            },
            "system": {
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "used_percent": memory.percent
                },
                "disk": {
                    "total": disk.total,
                    "free": disk.free,
                    "used_percent": disk.percent
                },
                "cpu": {
                    "usage_percent": psutil.cpu_percent(interval=0.1),
                    "count": psutil.cpu_count()
                }
            }
        })


class MetricsViewSet(viewsets.ViewSet):
    """
    ViewSet for performance metrics and monitoring data
    """
    permission_classes = [IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def performance(self, request):
        """
        Get performance metrics for the API
        """
        days = int(request.query_params.get('days', 7))
        start_date = timezone.now() - timezone.timedelta(days=days)
        
        # Get API response time metrics
        response_time_metrics = PerformanceMetric.objects.filter(
            metric_type='RESPONSE_TIME',
            timestamp__gte=start_date
        ).values('timestamp__date').annotate(
            avg_value=Avg('value'),
            max_value=Max('value'),
            min_value=Min('value')
        ).order_by('timestamp__date')
        
        # Get request count metrics
        request_counts = RequestLog.objects.filter(
            created_at__gte=start_date
        ).values('created_at__date').annotate(
            count=Count('id'),
            avg_response_time=Avg('response_time_ms')
        ).order_by('created_at__date')
        
        # Get error counts
        error_counts = ErrorLog.objects.filter(
            created_at__gte=start_date
        ).values('created_at__date').annotate(
            count=Count('id')
        ).order_by('created_at__date')
        
        # Get status code distribution
        status_codes = RequestLog.objects.filter(
            created_at__gte=start_date
        ).values('status_code').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Create time-series data structure
        date_range = [(start_date + timezone.timedelta(days=i)).date() for i in range(days + 1)]
        time_series = []
        
        for date in date_range:
            # Find matching metrics for this date
            response_time = next((m for m in response_time_metrics if m['timestamp__date'] == date), None)
            request_count = next((r for r in request_counts if r['created_at__date'] == date), None)
            error_count = next((e for e in error_counts if e['created_at__date'] == date), None)
            
            time_series.append({
                'date': date.isoformat(),
                'requests': request_count['count'] if request_count else 0,
                'avg_response_time': request_count['avg_response_time'] if request_count and request_count['avg_response_time'] else 0,
                'errors': error_count['count'] if error_count else 0,
                'response_time_avg': response_time['avg_value'] if response_time else 0,
                'response_time_max': response_time['max_value'] if response_time else 0,
                'response_time_min': response_time['min_value'] if response_time else 0
            })
        
        return Response({
            'time_series': time_series,
            'status_codes': status_codes,
            'summary': {
                'total_requests': sum(t['requests'] for t in time_series),
                'total_errors': sum(t['errors'] for t in time_series),
                'avg_response_time': sum(t['avg_response_time'] for t in time_series) / len(time_series) if time_series else 0,
                'error_rate': sum(t['errors'] for t in time_series) / sum(t['requests'] for t in time_series) * 100 if sum(t['requests'] for t in time_series) > 0 else 0
            }
        })
    
    @action(detail=False, methods=['get'])
    def system(self, request):
        """
        Get system resource metrics (CPU, memory, disk)
        """
        days = int(request.query_params.get('days', 7))
        start_date = timezone.now() - timezone.timedelta(days=days)
        
        # Get CPU metrics
        cpu_metrics = PerformanceMetric.objects.filter(
            metric_type='CPU',
            timestamp__gte=start_date
        ).values('timestamp__date').annotate(
            avg_value=Avg('value'),
            max_value=Max('value'),
            min_value=Min('value')
        ).order_by('timestamp__date')
        
        # Get memory metrics
        memory_metrics = PerformanceMetric.objects.filter(
            metric_type='MEMORY',
            timestamp__gte=start_date
        ).values('timestamp__date').annotate(
            avg_value=Avg('value'),
            max_value=Max('value'),
            min_value=Min('value')
        ).order_by('timestamp__date')
        
        # Create time-series data structure
        date_range = [(start_date + timezone.timedelta(days=i)).date() for i in range(days + 1)]
        time_series = []
        
        for date in date_range:
            # Find matching metrics for this date
            cpu = next((m for m in cpu_metrics if m['timestamp__date'] == date), None)
            memory = next((m for m in memory_metrics if m['timestamp__date'] == date), None)
            
            time_series.append({
                'date': date.isoformat(),
                'cpu_avg': cpu['avg_value'] if cpu else 0,
                'cpu_max': cpu['max_value'] if cpu else 0,
                'cpu_min': cpu['min_value'] if cpu else 0,
                'memory_avg': memory['avg_value'] if memory else 0,
                'memory_max': memory['max_value'] if memory else 0,
                'memory_min': memory['min_value'] if memory else 0
            })
        
        # Get current system stats
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return Response({
            'time_series': time_series,
            'current': {
                'cpu': {
                    'usage_percent': psutil.cpu_percent(interval=0.1),
                    'count': psutil.cpu_count(),
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'used_percent': memory.percent
                },
                'disk': {
                    'total': disk.total,
                    'free': disk.free,
                    'used_percent': disk.percent
                }
            }
        })


class LogsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for system and request logs
    """
    permission_classes = [IsAdminUser]
    
    @action(detail=False, methods=['get'], url_path='requests')
    def request_logs(self, request):
        """
        Get request logs with filtering
        """
        # Parse filters
        path = request.query_params.get('path')
        method = request.query_params.get('method')
        status_code = request.query_params.get('status_code')
        user_id = request.query_params.get('user')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        limit = int(request.query_params.get('limit', 100))
        
        # Build query
        query = RequestLog.objects.all()
        
        if path:
            query = query.filter(path__contains=path)
        
        if method:
            query = query.filter(method=method)
        
        if status_code:
            query = query.filter(status_code=status_code)
        
        if user_id:
            query = query.filter(user_id=user_id)
        
        if date_from:
            try:
                date_from = datetime.datetime.fromisoformat(date_from)
                query = query.filter(created_at__gte=date_from)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to = datetime.datetime.fromisoformat(date_to)
                query = query.filter(created_at__lte=date_to)
            except ValueError:
                pass
        
        # Execute query
        logs = query.order_by('-created_at')[:limit]
        
        # Prepare response
        result = [{
            'id': log.id,
            'path': log.path,
            'method': log.method,
            'status_code': log.status_code,
            'response_time_ms': log.response_time_ms,
            'user_id': log.user_id,
            'ip_address': log.ip_address,
            'created_at': log.created_at.isoformat()
        } for log in logs]
        
        return Response({
            'count': len(result),
            'logs': result
        })
    
    @action(detail=False, methods=['get'], url_path='errors')
    def error_logs(self, request):
        """
        Get error logs with filtering
        """
        # Parse filters
        path = request.query_params.get('path')
        error_type = request.query_params.get('error_type')
        user_id = request.query_params.get('user')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        limit = int(request.query_params.get('limit', 100))
        
        # Build query
        query = ErrorLog.objects.all()
        
        if path:
            query = query.filter(path__contains=path)
        
        if error_type:
            query = query.filter(error_type__contains=error_type)
        
        if user_id:
            query = query.filter(user_id=user_id)
        
        if date_from:
            try:
                date_from = datetime.datetime.fromisoformat(date_from)
                query = query.filter(created_at__gte=date_from)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to = datetime.datetime.fromisoformat(date_to)
                query = query.filter(created_at__lte=date_to)
            except ValueError:
                pass
        
        # Execute query
        logs = query.order_by('-created_at')[:limit]
        
        # Prepare response
        result = [{
            'id': log.id,
            'path': log.path,
            'method': log.method,
            'error_type': log.error_type,
            'error_message': log.error_message,
            'user_id': log.user_id,
            'ip_address': log.ip_address,
            'created_at': log.created_at.isoformat()
        } for log in logs]
        
        return Response({
            'count': len(result),
            'logs':
