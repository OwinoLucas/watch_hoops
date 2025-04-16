from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse
from django.utils import timezone
from typing import Dict, List, Any, Optional, Set

class Category(models.Model):
    """
    Represents a category for grouping news articles.
    
    Categories help organize content and allow users to browse
    related articles more easily.
    """
    name = models.CharField(
        max_length=100, 
        unique=True,
        db_index=True,
        help_text="Name of the category"
    )
    slug = models.SlugField(
        unique=True,
        db_index=True,
        help_text="URL-friendly version of the category name"
    )
    description = models.TextField(
        blank=True,
        help_text="Brief description of the category"
    )
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='subcategories',
        help_text="Parent category if this is a subcategory"
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order of the category"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['parent']),
        ]
    
    def __str__(self) -> str:
        """Return a string representation of the category."""
        return self.name
    
    def save(self, *args, **kwargs):
        """Generate slug from name if not provided."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self) -> str:
        """Get URL for category page."""
        return reverse('news:category_detail', kwargs={'slug': self.slug})
    
    def get_article_count(self) -> int:
        """Get the number of articles in this category."""
        return self.articles.filter(is_published=True).count()


class Tag(models.Model):
    """
    Represents a tag for categorizing articles.
    
    Tags provide a flexible way to categorize content across
    different categories and improve content discoverability.
    """
    name = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Name of the tag"
    )
    slug = models.SlugField(
        unique=True,
        db_index=True,
        help_text="URL-friendly version of the tag name"
    )
    description = models.TextField(
        blank=True,
        help_text="Brief description of what this tag represents"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
        ]
    
    def __str__(self) -> str:
        """Return a string representation of the tag."""
        return self.name
    
    def save(self, *args, **kwargs):
        """Generate slug from name if not provided."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self) -> str:
        """Get URL for tag page."""
        return reverse('news:tag_detail', kwargs={'slug': self.slug})
    
    def get_article_count(self) -> int:
        """Get the number of articles with this tag."""
        return self.articles.filter(is_published=True).count()


class Article(models.Model):
    """
    Represents a news article.
    
    This model stores comprehensive information about news articles, including:
    - Content information (title, body, excerpt)
    - SEO metadata
    - Publication status and schedule
    - Categories and tags
    - Media attachments
    - View tracking
    
    Related models:
    - Category: Categories this article belongs to
    - Tag: Tags associated with this article
    - Comment: User comments on this article
    - accounts.CustomUser: Author of the article
    """
    # Content Information
    title = models.CharField(
        max_length=200,
        db_index=True,
        help_text="Title of the article"
    )
    slug = models.SlugField(
        unique=True,
        max_length=255,
        db_index=True,
        help_text="URL-friendly version of the title"
    )
    content = models.TextField(
        help_text="Main content of the article"
    )
    excerpt = models.TextField(
        blank=True,
        help_text="Short summary of the article"
    )
    
    # Media
    featured_image = models.ImageField(
        upload_to='news/images/%Y/%m/',
        null=True,
        blank=True,
        help_text="Main image for the article"
    )
    featured_image_caption = models.CharField(
        max_length=255,
        blank=True,
        help_text="Caption for the featured image"
    )
    
    # Categories and Tags
    categories = models.ManyToManyField(
        Category,
        related_name='articles',
        blank=True,
        help_text="Categories this article belongs to"
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='articles',
        blank=True,
        help_text="Tags associated with this article"
    )
    
    # SEO Fields
    meta_description = models.CharField(
        max_length=160,
        blank=True,
        help_text="Description for search engines (max 160 characters)"
    )
    meta_keywords = models.CharField(
        max_length=255,
        blank=True,
        help_text="Keywords for search engines (comma-separated)"
    )
    
    # Publishing Information
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='articles',
        help_text="User who wrote the article"
    )
    is_published = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether the article is publicly visible"
    )
    is_featured = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether to feature this article on the homepage"
    )
    is_breaking = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether this is breaking news"
    )
    published_date = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="When the article was/will be published"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Statistics
    view_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times this article has been viewed"
    )
    
    # Related Content
    related_articles = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        related_name='related_to',
        help_text="Other articles related to this one"
    )
    
    # Social Media
    social_title = models.CharField(
        max_length=100,
        blank=True,
        help_text="Alternative title for social media sharing"
    )
    social_description = models.TextField(
        blank=True,
        help_text="Alternative description for social media sharing"
    )
    social_image = models.ImageField(
        upload_to='news/social/%Y/%m/',
        null=True,
        blank=True,
        help_text="Alternative image for social media sharing"
    )
    
    class Meta:
        verbose_name = "Article"
        verbose_name_plural = "Articles"
        ordering = ['-is_featured', '-published_date']
        indexes = [
            models.Index(fields=['-published_date']),
            models.Index(fields=['slug']),
            models.Index(fields=['author']),
            models.Index(fields=['is_published', '-published_date']),
            models.Index(fields=['is_featured', '-published_date']),
        ]
    
    def __str__(self) -> str:
        """Return a string representation of the article."""
        return self.title
    
    def save(self, *args, **kwargs):
        """Handle slug generation and publication date."""
        if not self.slug:
            self.slug = slugify(self.title)
            
        # Set published date when article is published
        if self.is_published and not self.published_date:
            self.published_date = timezone.now()
            
        # Auto-generate meta description if not provided
        if not self.meta_description and self.excerpt:
            self.meta_description = self.excerpt[:157] + '...' if len(self.excerpt) > 160 else self.excerpt
            
        super().save(*args, **kwargs)
    
    def get_absolute_url(self) -> str:
        """Get URL for article detail page."""
        return reverse('news:article_detail', kwargs={'slug': self.slug})
    
    def increment_view_count(self) -> None:
        """Increment the view count for this article."""
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def is_published_future(self) -> bool:
        """Check if article is scheduled for future publishing."""
        return self.is_published and self.published_date and self.published_date > timezone.now()
    
    def get_related_articles(self, limit: int = 3):
        """
        Get related articles based on explicit relationships,
        shared categories, and tags.
        
        Args:
            limit: Maximum number of articles to return
            
        Returns:
            QuerySet: Related articles
        """
        # Start with explicitly related articles
        related = list(self.related_articles.filter(is_published=True)[:limit])
        
        # If we need more, find articles in the same categories
        if len(related) < limit and self.categories.exists():
            category_articles = Article.objects.filter(
                is_published=True,
                categories__in=self.categories.all()
            ).exclude(
                id__in=[self.id] + [a.id for a in related]
            ).distinct()[:limit-len(related)]
            
            related.extend(list(category_articles))
            
        # If we still need more, find articles with the same tags
        if len(related) < limit and self.tags.exists():
            tag_articles = Article.objects.filter(
                is_published=True,
                tags__in=self.tags.all()
            ).exclude(
                id__in=[self.id] + [a.id for a in related]
            ).distinct()[:limit-len(related)]
            
            related.extend(list(tag_articles))
            
        return related[:limit]
    
    @property
    def reading_time(self) -> int:
        """
        Estimate reading time in minutes.
        
        Returns:
            int: Estimated reading time in minutes
        """
        words_per_minute = 200
        words = len(self.content.split())
        return max(1, round(words / words_per_minute))


class Comment(models.Model):
    """
    Represents a user comment on an article.
    
    This model tracks user comments, allowing for nested discussions
    through parent-child relationships.
    
    Related models:
    - Article: The article being commented on
    - accounts.CustomUser: The user who made the comment
    - Comment: Parent comment (if this is a reply)
    """
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='comments',
        help_text="Article being commented on"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='news_comments',
        help_text="User who wrote the comment"
    )
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='replies',
        help_text="Parent comment if this is a reply"
    )
    content = models.TextField(
        help_text="Content of the comment"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether the comment is approved and visible"
    )
    
    class Meta:
        verbose_name = "Comment"
        verbose_name_plural = "Comments"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['article', '-created_at']),
            models.Index(fields=['author']),
            models.Index(fields=['parent']),
            models.Index(fields=['is_approved']),
        ]
    
    def __str__(self) -> str:
        """Return a string representation of the comment."""
        return f"Comment by {self.author.get_full_name()} on {self.article.title}"
    
    def approve(self) -> None:
        """Approve the comment, making it visible."""
        self.is_approved = True
        self.save(update_fields=['is_approved'])
    
    @property
    def is_reply(self) -> bool:
        """Check if this comment is a reply to another comment."""
        return self.parent is not None
    
    def get_replies(self, approved_only: bool = True):
        """
        Get replies to this comment.
        
        Args:
            approved_only: Whether to only include approved replies
            
        Returns:
            QuerySet: Replies to this comment
        """
        if approved_only:
            return self.replies.filter(is_approved=True)
        return self.replies.all()


class ArticleView(models.Model):
    """
    Tracks individual views of articles.
    
    This model provides more detailed analytics about article views,
    including user information (if available) and device details.
    
    Related models:
    - Article: The viewed article
    - accounts.CustomUser: The user who viewed the article (if authenticated)
    """
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='views',
        help_text="The article that was viewed"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='article_views',
        help_text="The user who viewed the article (if authenticated)"
    )
    session_id = models.CharField(
        max_length=40,
        blank=True,
        null=True,
        help_text="Session ID for anonymous users"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the viewer"
    )
    user_agent = models.TextField(
        blank=True,
        help_text="User agent string from the viewer's browser"
    )
    device_type = models.CharField(
        max_length=20,
        blank=True,
        help_text="Type of device (desktop, mobile, tablet, etc.)"
    )
    browser = models.CharField(
        max_length=50,
        blank=True,
        help_text="Browser used to view the article"
    )
    os = models.CharField(
        max_length=50,
        blank=True,
        help_text="Operating system of the viewer"
    )
    referrer = models.URLField(
        max_length=500,
        blank=True,
        help_text="URL that referred the viewer to this article"
    )
    time_spent = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Time spent viewing the article in seconds"
    )
    viewed_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When the article was viewed"
    )
    
    class Meta:
        verbose_name = "Article View"
        verbose_name_plural = "Article Views"
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['article', '-viewed_at']),
            models.Index(fields=['user', '-viewed_at']),
            models.Index(fields=['session_id']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['device_type']),
        ]
    
    def __str__(self) -> str:
        """Return a string representation of the article view."""
        viewer = self.user.get_full_name() if self.user else "Anonymous"
        return f"View of '{self.article.title}' by {viewer} on {self.viewed_at.strftime('%Y-%m-%d %H:%M')}"
    
    @classmethod
    def record_view(cls, article, request, time_spent=None):
        """
        Record a view of an article.
        
        Args:
            article: The article being viewed
            request: The HTTP request object
            time_spent: Time spent viewing the article in seconds
            
        Returns:
            ArticleView: The created view record
        """
        user = request.user if request.user.is_authenticated else None
        session_id = request.session.session_key
        
        # Get IP address, handling potential proxy servers
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
        if 'Chrome' in user_agent:
            browser = 'Chrome'
        elif 'Firefox' in user_agent:
            browser = 'Firefox'
        elif 'Safari' in user_agent:
            browser = 'Safari'
        elif 'Edge' in user_agent:
            browser = 'Edge'
        elif 'MSIE' in user_agent or 'Trident' in user_agent:
            browser = 'Internet Explorer'
        
        # Simple OS detection
        os = 'unknown'
        if 'Windows' in user_agent:
            os = 'Windows'
        elif 'Macintosh' in user_agent:
            os = 'MacOS'
        elif 'Linux' in user_agent and 'Android' not in user_agent:
            os = 'Linux'
        elif 'Android' in user_agent:
            os = 'Android'
        elif 'iOS' in user_agent or 'iPhone' in user_agent or 'iPad' in user_agent:
            os = 'iOS'
        
        # Get referrer
        referrer = request.META.get('HTTP_REFERER', '')[:500]  # Limit to field size
        
        # Create the view record
        view = cls.objects.create(
            article=article,
            user=user,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            device_type=device_type,
            browser=browser,
            os=os,
            referrer=referrer,
            time_spent=time_spent
        )
        
        # Also increment the article's view counter
        article.increment_view_count()
        
        return view
