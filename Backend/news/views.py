from django.shortcuts import render
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Article
from .serializers import ArticleSerializer
from permissions import IsAdminOrReadOnly

class ArticleViewSet(viewsets.ModelViewSet):
    """
    Handles CRUD operations for News Articles
    GET /api/news/articles/ - List all articles
    GET /api/news/articles/{id}/ - Get specific article
    POST /api/news/articles/ - Create new article
    PUT /api/news/articles/{id}/ - Update article
    DELETE /api/news/articles/{id}/ - Delete article
    """
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'content']
    ordering_fields = ['published_date', 'title']

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """
        GET /api/news/articles/featured/ - Get featured articles
        """
        featured_articles = Article.objects.filter(is_featured=True)
        serializer = self.get_serializer(featured_articles, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def latest(self, request):
        """
        GET /api/news/articles/latest/ - Get latest articles
        """
        latest_articles = Article.objects.order_by('-published_date')[:5]
        serializer = self.get_serializer(latest_articles, many=True)
        return Response(serializer.data)
# Create your views here.
