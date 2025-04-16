from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from django.db.models import Q

from players.models import Player
from teams.models import Team, League
from games.models import Game
from news.models import Article, Category, Tag
from accounts.models import CustomUser


@registry.register_document
class PlayerDocument(Document):
    """Elasticsearch document for Player model"""
    
    team = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField(),
    })
    
    user = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'first_name': fields.TextField(),
        'last_name': fields.TextField(),
    })
    
    # Custom field for player name
    name = fields.TextField()
    
    class Index:
        name = 'players'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }
        
    class Django:
        model = Player
        fields = [
            'id',
            'position',
            'jersey_number',
            'nationality',
            'date_of_birth',
            'height_cm',
            'weight_kg',
        ]
        
        related_models = ['team', 'user']
        
    def prepare_name(self, instance):
        """Combine user's first and last name to create player name"""
        if instance.user:
            return f"{instance.user.first_name} {instance.user.last_name}".strip()
        return ""
    
    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Team):
            return related_instance.players.all()
        elif isinstance(related_instance, CustomUser):
            return Player.objects.filter(user=related_instance)
        return []


@registry.register_document
class TeamDocument(Document):
    """Elasticsearch document for Team model"""
    
    league = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField(),
    })
    
    class Index:
        name = 'teams'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }
        
    class Django:
        model = Team
        fields = [
            'id',
            'name',
            'home_venue',
            'founded_year',
            'description',
            'team_colors',
        ]
        
        related_models = ['league']
        
    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, League):
            return related_instance.teams.all()


@registry.register_document
class GameDocument(Document):
    """Elasticsearch document for Game model"""
    
    home_team = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField(),
    })
    
    away_team = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField(),
    })
    
    league = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField(),
    })
    
    status = fields.TextField()
    
    class Index:
        name = 'games'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }
        
    class Django:
        model = Game
        fields = [
            'id',
            'date_time',
            'venue',
            'home_score',
            'away_score',
        ]
        
        related_models = ['home_team', 'away_team', 'league']
        
    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Team):
            return Game.objects.filter(
                Q(home_team=related_instance) | 
                Q(away_team=related_instance)
            )
        elif isinstance(related_instance, League):
            return related_instance.matches.all()
        return []


@registry.register_document
class ArticleDocument(Document):
    """Elasticsearch document for Article model"""
    
    author = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'username': fields.TextField(),
    })
    
    categories = fields.NestedField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField(),
    })
    
    tags = fields.NestedField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField(),
    })
    
    class Index:
        name = 'articles'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }
        
    class Django:
        model = Article
        fields = [
            'id',
            'title',
            'content',
            'published_date',
            'is_featured',
            'meta_description',
            'meta_keywords',
        ]
        
        related_models = ['author', 'categories', 'tags']
        
    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, CustomUser):
            return related_instance.articles.all()
        elif isinstance(related_instance, Category):
            return related_instance.articles.all()
        elif isinstance(related_instance, Tag):
            return related_instance.articles.all()
        return []
