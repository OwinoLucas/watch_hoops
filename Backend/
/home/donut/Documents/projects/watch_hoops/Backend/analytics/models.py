        stats = MatchStats.objects.filter(player=self.player).order_by('-match__date_time')[:10]
        recent_stats = MatchStats.objects.filter(
            player=self.player, 
            match__date_time__date__gte=mid_point,
            match__date_time__date__lte=now
        )
        older_stats = MatchStats.objects.filter(
            player=self.player,
            match__date_time__date__gte=start_date,
            match__date_time__date__lt=mid_point
        )
        vs_opponent_stats = MatchStats.objects.filter(
            player=self.player,
            match__home_team=opponent
        ).order_by('-match__date_time')[:5]
        recent_stats = MatchStats.objects.filter(
            player=self.player
        ).order_by('-match__date_time')[:10]
