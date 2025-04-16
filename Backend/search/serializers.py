
from rest_framework import serializers
from players.models import Player
from teams.models import Team
from games.models import Game
from news.models import Article


class PlayerSearchSerializer(serializers.ModelSerializer):
    """Serializer for player search results"""
    team_name = serializers.SerializerMethodField()
    object_type = serializers.SerializerMethodField()
    
    class Meta:
        model = Player
        fields = [
            'id', 
            'name', 
            'position', 
            'jersey_number', 
            'team_name',
            'object_type'
        ]
    
    def get_team_name(self, obj):
        return obj.team.name if obj.team else None
    
    def get_object_type(self, obj):
        return 'player'


class TeamSearchSerializer(serializers.ModelSerializer):
    """Serializer for team search results"""
    league_name = serializers.SerializerMethodField()
    object_type = serializers.SerializerMethodField()
    
    class Meta:
        model = Team
        fields = [
            'id', 
            'name', 
            'home_venue', 
            'founded_year',
            'league_name',
            'object_type'
        ]
    
    def get_league_name(self, obj):
        return obj.league.name if obj.league else None
    
    def get_object_type(self, obj):
        return 'team'


class GameSearchSerializer(serializers.ModelSerializer):
    """Serializer for game search results"""
    home_team_name = serializers.SerializerMethodField()
    away_team_name = serializers.SerializerMethodField()
    object_type = serializers.SerializerMethodField()
    
    class Meta:
        model = Game
        fields = [
            'id',
            'date_time',
            'venue',
            'status',
            'home_team_name',
            'away_team_name',
            'object_type'
        ]
    
    def get_home_team_name(self, obj):
        return obj.home_team.name
    
    def get_away_team_name(self, obj):
        return obj.away_team.name
    
    def get_object_type(self, obj):
        return 'game'


class ArticleSearchSerializer(serializers.ModelSerializer):
    """Serializer for article search results"""
    author_name = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()
    object_type = serializers.SerializerMethodField()
    
    class Meta:
        model = Article
        fields = [
            'id',
            'title',
            'published_date',
            'author_name',
            'categories',
            'is_featured',
            'object_type'
        ]
    
    def get_author_name(self, obj):
        return obj.author.get_full_name() if obj.author else None
    
    def get_categories(self, obj):
        return [category.name for category in obj.categories.all()]
    
    def get_object_type(self, obj):
        return 'article'


class GlobalSearchSerializer(serializers.Serializer):
    """
    Serializer for combined search results across multiple models
    """
    players = PlayerSearchSerializer(many=True, read_only=True)
    teams = TeamSearchSerializer(many=True, read_only=True)
    games = GameSearchSerializer(many=True, read_only=True)
    articles = ArticleSearchSerializer(many=True, read_only=True)
    
    def to_representation(self, instance):
        # Convert to unified format for frontend
        results = []
        
        for player in instance.get('players', []):
            serialized = PlayerSearchSerializer(player).data
            results.append(serialized)
            
        for team in instance.get('teams', []):
            serialized = TeamSearchSerializer(team).data
            results.append(serialized)
            
        for game in instance.get('games', []):
            serialized = GameSearchSerializer(game).data
            results.append(serialized)
            
        for article in instance.get('articles', []):
            serialized = ArticleSearchSerializer(article).data
            results.append(serialized)
        
        return {
            'count': len(results),
            'results': results
        }

