    
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
            return related_instance.articles.all()
        elif isinstance(related_instance, Category):
            return related_instance.articles.all()
        elif isinstance(related_instance, Tag):
            return related_instance.articles.all()
        return []
