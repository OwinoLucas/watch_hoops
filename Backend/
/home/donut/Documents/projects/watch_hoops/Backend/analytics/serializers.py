        model = GamePrediction
        fields = '__all__'

class PlayerPerformancePredictionSerializer(serializers.ModelSerializer):
    player = PlayerSerializer(read_only=True)
    game = GameSerializer(read_only=True)
    
    class Meta:
        model = PlayerPerformancePrediction
        fields = '__all__'

class TeamPerformanceTrendSerializer(serializers.ModelSerializer):
    team = TeamSerializer(read_only=True)
    
    class Meta:
        model = TeamPerformanceTrend
        fields = '__all__'
