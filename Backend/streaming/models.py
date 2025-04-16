from django.db import models
from django.conf import settings
from django.utils import timezone
from typing import Dict, List, Any, Optional, Tuple
import uuid

class StreamingPlan(models.Model):
    """
    Represents a subscription plan for streaming access.
    
    This model defines different streaming subscription options with
    varying features, quality settings, and pricing.
    
    Users can subscribe to plans to gain access to live game streams
    according to the plan's permissions and restrictions.
    """
    QUALITY_CHOICES = (
        ('SD', 'Standard Definition (480p)'),
        ('HD', 'High Definition (720p)'),
        ('FHD', 'Full HD (1080p)'),
        ('UHD', '4K Ultra HD'),
    )
    
    # Plan details
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Name of the streaming plan"
    )
    description = models.TextField(
        help_text="Detailed description of the plan and its features"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Monthly price of the plan"
    )
    duration_days = models.PositiveIntegerField(
        default=30,
        help_text="Duration of the plan in days"
    )
    
    # Quality settings
    max_quality = models.CharField(
        max_length=3,
        choices=QUALITY_CHOICES,
        default='HD',
        help_text="Maximum streaming quality allowed by this plan"
    )
    max_devices = models.PositiveSmallIntegerField(
        default=1,
        help_text="Maximum number of devices that can stream simultaneously"
    )
    
    # Feature flags
    allows_dvr = models.BooleanField(
        default=False,
        help_text="Whether the plan allows DVR/recording capabilities"
    )
    allows_downloads = models.BooleanField(
        default=False,
        help_text="Whether the plan allows downloading for offline viewing"
    )
    allows_chat = models.BooleanField(
        default=True,
        help_text="Whether the plan allows access to live chat during streams"
    )
    allows_multiple_angles = models.BooleanField(
        default=False,
        help_text="Whether the plan allows viewing multiple camera angles"
    )
    
    # Status tracking
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this plan is currently available for purchase"
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Whether to feature this plan in promotions"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Streaming Plan"
        verbose_name_plural = "Streaming Plans"
        ordering = ['price']
        indexes = [
            models.Index(fields=['is_active', 'price']),
            models.Index(fields=['max_quality']),
        ]
    
    def __str__(self) -> str:
        """Return a string representation of the streaming plan."""
        return f"{self.name} (${self.price})"
    
    @property
    def quality_display(self) -> str:
        """Get a human-readable display of the maximum quality."""
        return dict(self.QUALITY_CHOICES).get(self.max_quality, self.max_quality)
    
    def has_feature(self, feature_name: str) -> bool:
        """
        Check if the plan has a specific feature.
        
        Args:
            feature_name: Name of the feature to check (e.g., 'allows_dvr')
            
        Returns:
            bool: Whether the plan has the feature
        """
        return getattr(self, feature_name, False)
    
    def get_features_list(self) -> List[str]:
        """
        Get a list of all features this plan includes.
        
        Returns:
            List[str]: List of available features
        """
        features = []
        
        if self.allows_dvr:
            features.append("DVR capability")
        if self.allows_downloads:
            features.append("Download for offline viewing")
        if self.allows_chat:
            features.append("Live chat")
        if self.allows_multiple_angles:
            features.append("Multiple camera angles")
            
        features.append(f"Up to {self.quality_display} quality")
        features.append(f"{self.max_devices} simultaneous device{'s' if self.max_devices > 1 else ''}")
        
        return features


class GameStream(models.Model):
    """
    Represents a live stream for a specific game.
    
    This model manages the technical details of streaming a basketball game,
    including configuration, status, and performance metrics.
    
    Related models:
    - games.Game: The game being streamed
    - StreamAccess: Access permissions for users
    - ViewerSession: Individual viewing sessions
    """
    STREAM_STATUS = (
        ('SCHEDULED', 'Scheduled'),
        ('PREPARING', 'Preparing'),
        ('LIVE', 'Live'),
        ('PAUSED', 'Paused'),
        ('ENDED', 'Ended'),
        ('TECHNICAL_DIFFICULTIES', 'Technical Difficulties'),
        ('CANCELLED', 'Cancelled'),
    )
    
    # Stream identification
    stream_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        help_text="Unique identifier for the stream"
    )
    game = models.OneToOneField(
        'games.Game',
        on_delete=models.CASCADE,
        related_name='stream',
        help_text="Game this stream is for"
    )
    title = models.CharField(
        max_length=200,
        help_text="Title of the stream"
    )
    
    # Configuration
    stream_url = models.URLField(
        help_text="URL to the video stream"
    )
    stream_key = models.CharField(
        max_length=255,
        unique=True,
        help_text="Secret key for stream authentication"
    )
    status = models.CharField(
        max_length=25,
        choices=STREAM_STATUS,
        default='SCHEDULED',
        db_index=True,
        help_text="Current status of the stream"
    )
    
    # Quality settings
    available_qualities = models.JSONField(
        default=list,
        help_text="List of available quality options"
    )
    default_quality = models.CharField(
        max_length=10,
        default='auto',
        help_text="Default quality setting for playback"
    )
    
    # Timing
    scheduled_start = models.DateTimeField(
        db_index=True,
        help_text="When the stream is scheduled to start"
    )
    actual_start = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the stream actually started"
    )
    actual_end = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the stream ended"
    )
    
    # Features
    chat_enabled = models.BooleanField(
        default=True,
        help_text="Whether live chat is enabled for this stream"
    )
    dvr_enabled = models.BooleanField(
        default=True,
        help_text="Whether DVR functionality is enabled"
    )
    multiple_angles = models.BooleanField(
        default=False,
        help_text="Whether multiple camera angles are available"
    )
    
    # Stats
    peak_viewers = models.PositiveIntegerField(
        default=0,
        help_text="Peak number of concurrent viewers"
    )
    total_viewers = models.PositiveIntegerField(
        default=0,
        help_text="Total number of unique viewers"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Game Stream"
        verbose_name_plural = "Game Streams"
        ordering = ['-scheduled_start']
        indexes = [
            models.Index(fields=['status', '-scheduled_start']),
            models.Index(fields=['game']),
            models.Index(fields=['stream_id']),
        ]
    
    def __str__(self) -> str:
        """Return a string representation of the game stream."""
        return f"Stream: {self.title} ({self.get_status_display()})"
    
    @property
    def is_live(self) -> bool:
        """Check if the stream is currently live."""
        return self.status == 'LIVE'
    
    @property
    def duration(self) -> Optional[int]:
        """
        Calculate the duration of the stream in minutes.
        
        Returns:
            int: Duration in minutes, or None if the stream hasn't ended
        """
        if not self.actual_start or not self.actual_end:
            return None
            
        delta = self.actual_end - self.actual_start
        return int(delta.total_seconds() / 60)
    
    def start_stream(self) -> None:
        """Mark the stream as live and record the start time."""
        self.status = 'LIVE'
        self.actual_start = timezone.now()
        self.save(update_fields=['status', 'actual_start', 'updated_at'])
    
    def end_stream(self) -> None:
        """Mark the stream as ended and record the end time."""
        self.status = 'ENDED'
        self.actual_end = timezone.now()
        self.save(update_fields=['status', 'actual_end', 'updated_at'])
    
    def pause_stream(self) -> None:
        """Mark the stream as paused."""
        self.status = 'PAUSED'
        self.save(update_fields=['status', 'updated_at'])
    
    def report_technical_difficulties(self) -> None:
        """Mark the stream as having technical difficulties."""
        self.status = 'TECHNICAL_DIFFICULTIES'
        self.save(update_fields=['status', 'updated_at'])
    
    def cancel_stream(self) -> None:
        """Mark the stream as cancelled."""
        self.status = 'CANCELLED'
        self.save(update_fields=['status', 'updated_at'])
    
    def update_viewer_count(self, current_viewers: int) -> None:
        """
        Update the peak viewer count if necessary.
        
        Args:
            current_viewers: Current number of viewers
        """
        if current_viewers > self.peak_viewers:
            self.peak_viewers = current_viewers
            self.save(update_fields=['peak_viewers', 'updated_at'])
    
    def increment_total_viewers(self) -> None:
        """Increment the total unique viewers count."""
        self.total_viewers += 1
        self.save(update_fields=['total_viewers', 'updated_at'])
    
    def get_current_viewers_count(self) -> int:
        """
        Get the current number of viewers.
        
        Returns:
            int: Current number of viewers
        """
        return self.viewer_sessions.filter(
            ended_at__isnull=True
        ).count()
    
    def get_available_qualities_display(self) -> str:
        """
        Get a human-readable list of available qualities.
        
        Returns:
            str: Comma-separated list of qualities
        """
        return ", ".join(self.available_qualities)


class StreamAccess(models.Model):
    """
    Represents a user's access to a specific game stream.
    
    This model manages permissions for viewers to access streams,
    tracking purchase information and access restrictions.
    
    Related models:
    - accounts.CustomUser: The user with access
    - GameStream: The stream being accessed
    - accounts.Payment: Payment record for this access
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='stream_accesses',
        help_text="User who has access to the stream"
    )
    stream = models.ForeignKey(
        GameStream,
        on_delete=models.CASCADE,
        related_name='viewer_accesses',
        help_text="Stream the user has access to"
    )
    access_code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique code granting access to the stream"
    )
    
    # Purchase information
    payment = models.OneToOneField(
        'accounts.Payment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stream_access',
        help_text="Payment record for this access"
    )
    is_paid = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether this access has been paid for"
    )
    is_complimentary = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether this is complimentary (free) access"
    )
    
    # Quality and restrictions
    max_quality = models.CharField(
        max_length=10,
        default='HD',
        help_text="Maximum quality allowed"
    )
    max_devices = models.PositiveSmallIntegerField(
        default=1,
        help_text="Maximum number of devices that can access simultaneously"
    )
    
    # Timing
    valid_from = models.DateTimeField(
        help_text="When access becomes valid"
    )
    valid_until = models.DateTimeField(
        help_text="When access expires"
    )
    
    # Usage tracking
    last_accessed = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the stream was last accessed"
    )
    access_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times the stream has been accessed"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Stream Access"
        verbose_name_plural = "Stream Accesses"
        unique_together = ['user', 'stream']
        indexes = [
            models.Index(fields=['user', 'valid_until']),
            models.Index(fields=['stream', 'is_paid']),
            models.Index(fields=['access_code']),
        ]
    
    def __str__(self) -> str:
        """Return a string representation of the stream access."""
        return f"Access for {self.user.get_full_name()} to {self.stream.title}"
    
    def save(self, *args, **kwargs):
        """Generate access code if not provided."""
        if not self.access_code:
            self.access_code = f"ACC-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    @property
    def is_active(self) -> bool:
        """
        Check if the access is currently active.
        
        Returns:
            bool: Whether the access is active
        """
        now = timezone.now()
        return (
            (self.is_paid or self.is_complimentary) and
            self.valid_from <= now and
            self.valid_until >= now
        )
    
    def record_access(self) -> None:
        """Record that the stream was accessed."""
        self.last_accessed = timezone.now()
        self.access_count += 1
        self.save(update_fields=['last_accessed', 'access_count', 'updated_at'])
    
    def extend_access(self, days: int) -> None:
        """
        Extend the validity period of the access.
        
        Args:
            days: Number of days to extend by
        """
        self.valid_until = self.valid_until + timezone.timedelta(days=days)
        self.save(update_fields=['valid_until', 'updated_at'])
    
    def get_active_sessions_count(self) -> int:
        """
        Get the number of active viewing sessions for this access.
        
        Returns:
            int: Number of active sessions
        """
        return self.viewer_sessions.filter(ended_at__isnull=True).count()
    
    def check_device_limit(self) -> bool:
        """
        Check if the user has reached their device limit.
        
        Returns:
            bool: True if under limit, False if at or over limit
        """
        current_devices = self.get_active_sessions_count()
        return current_devices < self.max_devices


class ViewerSession(models.Model):
    """
    Represents a viewing session for a stream.
    
    This model tracks individual viewing sessions, including:
    - Session timing and duration
    - Quality and performance metrics
    - Connection statistics
    - Error tracking
    - Device information
    
    Related models:
    - StreamAccess: The access permission for this session
    - GameStream: The stream being viewed
    - accounts.CustomUser: The user viewing the stream
    """
    # Session identification
    session_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        help_text="Unique identifier for this viewing session"
    )
    stream_access = models.ForeignKey(
        StreamAccess,
        on_delete=models.CASCADE,
        related_name='viewer_sessions',
        help_text="Access permission for this session"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='stream_sessions',
        help_text="User viewing the stream"
    )
    stream = models.ForeignKey(
        GameStream,
        on_delete=models.CASCADE,
        related_name='viewer_sessions',
        help_text="Stream being viewed"
    )
    
    # Timing
    started_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When the viewing session started"
    )
    ended_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the viewing session ended"
    )
    last_activity = models.DateTimeField(
        auto_now=True,
        help_text="When the session was last active"
    )
    
    # Quality metrics
    selected_quality = models.CharField(
        max_length=10,
        default='auto',
        help_text="Quality level selected by the user"
    )
    average_bitrate = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Average bitrate during playback (kbps)"
    )
    average_framerate = models.FloatField(
        null=True,
        blank=True,
        help_text="Average framerate during playback (fps)"
    )
    
    # Connection statistics
    connection_type = models.CharField(
        max_length=20,
        blank=True,
        help_text="Type of connection (wifi, cellular, etc.)"
    )
    isp = models.CharField(
        max_length=100,
        blank=True,
        help_text="Internet Service Provider"
    )
    buffer_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of buffering events"
    )
    total_buffer_duration = models.PositiveIntegerField(
        default=0,
        help_text="Total buffering time in seconds"
    )
    
    # Performance metrics
    latency = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Average latency in milliseconds"
    )
    dropped_frames = models.PositiveIntegerField(
        default=0,
        help_text="Number of dropped frames"
    )
    
    # Error tracking
    error_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of playback errors"
    )
    last_error = models.CharField(
        max_length=255,
        blank=True,
        help_text="Last error message"
    )
    last_error_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the last error occurred"
    )
    
    # Device information
    device_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="Type of device (desktop, mobile, tablet, etc.)"
    )
    browser = models.CharField(
        max_length=50,
        blank=True,
        help_text="Browser used"
    )
    os = models.CharField(
        max_length=50,
        blank=True,
        help_text="Operating system"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the viewer"
    )
    user_agent = models.TextField(
        blank=True,
        help_text="User agent string"
    )
    
    # Chat participation
    chat_messages_sent = models.PositiveIntegerField(
        default=0,
        help_text="Number of chat messages sent during the session"
    )
    
    class Meta:
        verbose_name = "Viewer Session"
        verbose_name_plural = "Viewer Sessions"
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', '-started_at']),
            models.Index(fields=['stream', '-started_at']),
            models.Index(fields=['stream_access']),
            models.Index(fields=['session_id']),
        ]
    
    def __str__(self) -> str:
        """Return a string representation of the viewer session."""
        return f"Session {self.session_id} - {self.user.get_full_name()}"
    
    @property
    def duration(self) -> Optional[int]:
        """
        Calculate session duration in seconds.
        
        Returns:
            int: Duration in seconds, or None if session is still active
        """
        if not self.ended_at:
            return None
            
        delta = self.ended_at - self.started_at
        return int(delta.total_seconds())
    
    @property
    def is_active(self) -> bool:
        """Check if the session is currently active."""
        return self.ended_at is None
    
    def end_session(self) -> None:
        """End the viewing session."""
        if not self.ended_at:
            self.ended_at = timezone.now()
            self.save(update_fields=['ended_at'])
    
    def record_buffer_event(self, duration_ms: int) -> None:
        """
        Record a buffering event.
        
        Args:
            duration_ms: Duration of buffering in milliseconds
        """
        self.buffer_count += 1
        self.total_buffer_duration += int(duration_ms / 1000)  # Convert to seconds
        self.save(update_fields=['buffer_count', 'total_buffer_duration'])
    
    def record_error(self, error_message: str) -> None:
        """
        Record a playback error.
        
        Args:
            error_message: Description of the error
        """
        self.error_count += 1
        self.last_error = error_message
        self.last_error_time = timezone.now()
        self.save(update_fields=['error_count', 'last_error', 'last_error_time'])
    
    def update_quality_metrics(self, bitrate: int, framerate: float) -> None:
        """
        Update quality metrics for the session.
        
        Args:
            bitrate: Current bitrate in kbps
            framerate: Current framerate in fps
        """
        # If first update, set as average
        if not self.average_bitrate:
            self.average_bitrate = bitrate
            self.average_framerate = framerate
        else:
            # Simple rolling average (could be improved with weighted average)
            self.average_bitrate = (self.average_bitrate + bitrate) // 2
            self.average_framerate = (self.average_framerate + framerate) / 2
            
        self.save(update_fields=['average_bitrate', 'average_framerate'])
    
    def increment_chat_messages(self) -> None:
        """Increment the count of chat messages sent."""
        self.chat_messages_sent += 1
        self.save(update_fields=['chat_messages_sent'])
    
    @classmethod
    def create_session(cls, stream_access, request, quality='auto'):
        """
        Create a new viewing session with device information.
        
        Args:
            stream_access: The StreamAccess permission
            request: The HTTP request object
            quality: Initial quality setting
            
        Returns:
            ViewerSession: The created session
        """
        # Record the access
        stream_access.record_access()
        
        # Get IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR', '')
        
        # Get user agent information
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Simple device type detection
        device_type = 'unknown'
        if 'Mobile' in user_agent:
            if 'Tablet' in user_agent or 'iPad' in user_agent:
                device_type = 'tablet'
            else:
                device_type = 'mobile'
        else:
            device_type = 'desktop'
        
        # Simple browser detection
        browser = 'unknown'
        if 'Chrome' in user_agent and 'Edg' not in user_agent:
            browser = 'Chrome'
        elif 'Firefox' in user_agent:
            browser = 'Firefox'
        elif 'Safari' in user_agent and 'Chrome' not in user_agent:
            browser = 'Safari'
        elif 'Edg' in user_agent:
            browser = 'Edge'
        elif 'MSIE' in user_agent or 'Trident' in user_agent:
            browser = 'Internet Explorer'
        else:
            browser = 'Other'
        
        # Simple OS detection
        os = 'unknown'
        if 'Windows' in user_agent:
            os = 'Windows'
        elif 'Macintosh' in user_agent or 'Mac OS' in user_agent:
            os = 'MacOS'
        elif 'Linux' in user_agent and 'Android' not in user_agent:
            os = 'Linux'
        elif 'Android' in user_agent:
            os = 'Android'
        elif 'iOS' in user_agent or 'iPhone' in user_agent or 'iPad' in user_agent:
            os = 'iOS'
        else:
            os = 'Other'
        
        # Determine connection type (simplified, would be more accurate with client-side data)
        connection_type = 'unknown'
        if device_type in ['mobile', 'tablet']:
            connection_type = 'mobile'
        else:
            connection_type = 'broadband'
        
        # Create the session
        session = cls.objects.create(
            stream_access=stream_access,
            user=stream_access.user,
            stream=stream_access.stream,
            selected_quality=quality,
            connection_type=connection_type,
            device_type=device_type,
            browser=browser,
            os=os,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Notify stream of new viewer
        stream_access.stream.increment_total_viewers()
        
        return session
