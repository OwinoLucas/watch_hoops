from django.db.models import Q
from django.http import JsonResponse
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import MultiMatch, Match, Term

from .serializers import (
    GlobalSearchSerializer,
    PlayerSearchSerializer,
    TeamSearchSerializer,
    GameSearchSerializer,
    ArticleSearchSerializer
)
from .models import SearchQuery
from players.models import Player
from teams.models import Team
from games.models import Game
from news.models import Article

from .documents import (
    PlayerDocument,
    TeamDocument, 
    GameDocument,
    ArticleDocument
)


class SearchViewSet(viewsets.ViewSet):
    """
    Viewset for search functionality
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def _log_search_query(self, request, query, results_count):
        """
        Log search query for analytics
        """
        user = request.user if request.user.is_authenticated else None
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')
        
        SearchQuery.objects.create(
            query=query,
            user=user,
            results_count=results_count,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @action(detail=False, methods=['get'], url_path='global')
    def global_search(self, request):
        """
        Search across all content types (players, teams, games, articles)
        """
        query = request.query_params.get('q', '')
        if not query or len(query) < 3:
            return Response(
                {"error": "Search query must be at least 3 characters long"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Define search parameters
        limit_per_type = int(request.query_params.get('limit', 5))
        search_types = request.query_params.getlist('type', ['player', 'team', 'game', 'article'])
        
        results = {}
        total_count = 0
        
        # Search in Players
        if 'player' in search_types:
            s = PlayerDocument.search()
            player_query = MultiMatch(
                query=query,
                fields=['name^3', 'position', 'nationality'],
                fuzziness='AUTO'
            )
            s = s.query(player_query)[:limit_per_type]
            player_hits = s.execute()
            
            # Get Django objects
            player_ids = [hit.meta.id for hit in player_hits]
            players = Player.objects.filter(id__in=player_ids)
            results['players'] = players
            total_count += len(players)
        else:
            results['players'] = []
            
        # Search in Teams
        if 'team' in search_types:
            s = TeamDocument.search()
            team_query = MultiMatch(
                query=query,
                fields=['name^3', 'home_venue', 'description'],
                fuzziness='AUTO'
            )
            s = s.query(team_query)[:limit_per_type]
            team_hits = s.execute()
            
            # Get Django objects
            team_ids = [hit.meta.id for hit in team_hits]
            teams = Team.objects.filter(id__in=team_ids)
            results['teams'] = teams
            total_count += len(teams)
        else:
            results['teams'] = []
            
        # Search in Games
        if 'game' in search_types:
            s = GameDocument.search()
            game_query = MultiMatch(
                query=query,
                fields=['venue^2', 'home_team.name', 'away_team.name'],
                fuzziness='AUTO'
            )
            s = s.query(game_query)[:limit_per_type]
            game_hits = s.execute()
            
            # Get Django objects
            game_ids = [hit.meta.id for hit in game_hits]
            games = Game.objects.filter(id__in=game_ids)
            results['games'] = games
            total_count += len(games)
        else:
            results['games'] = []
            
        # Search in Articles
        if 'article' in search_types:
            s = ArticleDocument.search()
            article_query = MultiMatch(
                query=query,
                fields=['title^3', 'content', 'meta_keywords^2'],
                fuzziness='AUTO'
            )
            s = s.query(article_query)[:limit_per_type]
            article_hits = s.execute()
            
            # Get Django objects
            article_ids = [hit.meta.id for hit in article_hits]
            articles = Article.objects.filter(id__in=article_ids)
            results['articles'] = articles
            total_count += len(articles)
        else:
            results['articles'] = []
            
        # Log the search query
        self._log_search_query(request, query, total_count)
        
        # Return combined results
        serializer = GlobalSearchSerializer(results)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='players')
    def player_search(self, request):
        """
        Search players only
        """
        query = request.query_params.get('q', '')
        if not query or len(query) < 2:
            return Response(
                {"error": "Search query must be at least 2 characters long"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Search in player document
        s = PlayerDocument.search()
        player_query = MultiMatch(
            query=query,
            fields=['name^3', 'position', 'nationality'],
            fuzziness='AUTO'
        )
        
        # Add filtering
        position = request.query_params.get('position')
        team_id = request.query_params.get('team')
        
        s = s.query(player_query)
        
        if position:
            s = s.filter('term', position=position)
        
        if team_id:
            s = s.filter('term', team__id=team_id)
            
        # Execute search
        limit = int(request.query_params.get('limit', 20))
        s = s[:limit]
        player_hits = s.execute()
        
        # Get Django objects
        player_ids = [hit.meta.id for hit in player_hits]
        players = Player.objects.filter(id__in=player_ids)
        
        # Log the search
        self._log_search_query(request, query, len(players))
        
        # Return results
        serializer = PlayerSearchSerializer(players, many=True)
        return Response({
            "count": len(players),
            "results": serializer.data
        })
    
    @action(detail=False, methods=['get'], url_path='teams')
    def team_search(self, request):
        """
        Search teams only
        """
        query = request.query_params.get('q', '')
        if not query or len(query) < 2:
            return Response(
                {"error": "Search query must be at least 2 characters long"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Search in team document
        s = TeamDocument.search()
        team_query = MultiMatch(
            query=query,
            fields=['name^3', 'home_venue', 'description'],
            fuzziness='AUTO'
        )
        
        # Add filtering
        league_id = request.query_params.get('league')
        
        s = s.query(team_query)
        
        if league_id:
            s = s.filter('term', league__id=league_id)
            
        # Execute search
        limit = int(request.query_params.get('limit', 20))
        s = s[:limit]
        team_hits = s.execute()
        
        # Get Django objects
        team_ids = [hit.meta.id for hit in team_hits]
        teams = Team.objects.filter(id__in=team_ids)
        
        # Log the search
        self._log_search_query(request, query, len(teams))
        
        # Return results
        serializer = TeamSearchSerializer(teams, many=True)
        return Response({
            "count": len(teams),
            "results": serializer.data
        })
    
    @action(detail=False, methods=['get'], url_path='games')
    def game_search(self, request):
        """
        Search games only
        """
        query = request.query_params.get('q', '')
        if not query or len(query) < 2:
            return Response(
                {"error": "Search query must be at least 2 characters long"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Search in game document
        s = GameDocument.search()
        game_query = MultiMatch(
            query=query,
            fields=['venue^2', 'home_team.name', 'away_team.name'],
            fuzziness='AUTO'
        )
        
        # Add filtering
        status_filter = request.query_params.get('status')
        team_id = request.query_params.get('team')
        
        s = s.query(game_query)
        
        if status_filter:
            s = s.filter('term', status=status_filter)
        
        if team_id:
            s = s.filter('bool', should=[
                {'term': {'home_team.id': team_id}},
                {'term': {'away_team.id': team_id}}
            ])
            
        # Execute search
        limit = int(request.query_params.get('limit', 20))
        s = s[:limit]
        game_hits = s.execute()
        
        # Get Django objects
        game_ids = [hit.meta.id for hit in game_hits]
        games = Game.objects.filter(id__in=game_ids)
        
        # Log the search
        self._log_search_query(request, query, len(games))
        
        # Return results
        serializer = GameSearchSerializer(games, many=True)
        return Response({
            "count": len(games),
            "results": serializer.data
        })
    
    @action(detail=False, methods=['get'], url_path='articles')
    def article_search(self, request):
        """
        Search articles only
        """
        query = request.query_params.get('q', '')
        if not query or len(query) < 2:
            return Response(
                {"error": "Search query must be at least 2 characters long"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Search in article document
        s = ArticleDocument.search()
        article_query = MultiMatch(
            query=query,
            fields=['title^3', 'content', 'meta_keywords^2'],
            fuzziness='AUTO'
        )
        
        # Add filtering
        featured = request.query_params.get('featured')
        category = request.query_params.get('category')
        
        s = s.query(article_query)
        
        if featured:
            s = s.filter('term', is_featured=featured.lower() == 'true')
        
        if category:
            s = s.filter('nested', path='categories', query=Q('term', categories__id=category))
            
        # Execute search
        limit = int(request.query_params.get('limit', 20))
        s = s[:limit]
        article_hits = s.execute()
        
        # Get Django objects
        article_ids = [hit.meta.id for hit in article_hits]
        articles = Article.objects.filter(id__in=article_ids)
        
        # Log the search
        self._log_search_query(request, query, len(articles))
        
        # Return results
        serializer = ArticleSearchSerializer(articles, many=True)
        return Response({
            "count": len(articles),
            "results": serializer.data
        })
    
    @action(detail=False, methods=['get'], url_path='suggestions')
    def search_suggestions(self, request):
        """
        Get search suggestions as user types
        """
        query = request.query_params.get('q', '')
        if not query:
            return Response([])
            
        # Get popular search queries that start with the input
        popular_queries = SearchQuery.objects.filter(
            query__istartswith=query
        ).values('query').annotate(
            count=Count('query')
        ).order_by('-count')[:5]
        
        suggestions = [item['query'] for item in popular_queries]
        
        # If we have fewer than 5 suggestions, add some from popular entities
        if len(suggestions) < 5:
            # Add popular player and team names
            s = PlayerDocument.search()
            player_query = MultiMatch(
                query=query,
                fields=['name'],
                fuzziness='AUTO'
            )
            s = s.query(player_query)[:3]
            player_hits = s.execute()
            
            for hit in player_hits:
                if len(suggestions) < 5 and hit.name not in suggestions:
                    suggestions.append(hit.name)
                    
            # Add popular team names
            if len(suggestions) < 5:
                s = TeamDocument.search()
                team_query = MultiMatch(
                    query=query,
                    fields=['name'],
                    fuzziness='AUTO'
                )
                s = s.query(team_query)[:3]
                team_hits = s.execute()
                
                for hit in team_hits:
                    if len(suggestions) < 5 and hit.name not in suggestions:
                        suggestions.append(hit.name)
        
        return Response(suggestions)
