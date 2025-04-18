# Generated by Django 5.1.8 on 2025-04-16 07:11

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('players', '0001_initial'),
        ('teams', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_time', models.DateTimeField(db_index=True, help_text='Scheduled date and time of the game')),
                ('venue', models.CharField(help_text='Location where the game will be played', max_length=200)),
                ('status', models.CharField(choices=[('SCHEDULED', 'Scheduled'), ('LIVE', 'Live'), ('FINISHED', 'Finished'), ('POSTPONED', 'Postponed')], db_index=True, default='SCHEDULED', help_text='Current status of the game', max_length=10)),
                ('home_score', models.IntegerField(blank=True, null=True)),
                ('away_team', models.ForeignKey(help_text='The visiting team', on_delete=django.db.models.deletion.CASCADE, related_name='away_matches', to='teams.team')),
                ('home_team', models.ForeignKey(help_text='The team hosting the game', on_delete=django.db.models.deletion.CASCADE, related_name='home_matches', to='teams.team')),
                ('league', models.ForeignKey(help_text='The league this game belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='matches', to='teams.league')),
            ],
            options={
                'verbose_name': 'Game',
                'verbose_name_plural': 'Games',
                'ordering': ['-date_time'],
            },
        ),
        migrations.CreateModel(
            name='MatchStats',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('points', models.IntegerField(default=0, help_text='Number of points scored')),
                ('assists', models.IntegerField(default=0, help_text='Number of assists')),
                ('rebounds', models.IntegerField(default=0, help_text='Number of rebounds')),
                ('steals', models.IntegerField(default=0, help_text='Number of steals')),
                ('blocks', models.IntegerField(default=0, help_text='Number of blocks')),
                ('turnovers', models.IntegerField(default=0, help_text='Number of turnovers')),
                ('minutes_played', models.IntegerField(default=0, help_text='Minutes played in the game')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('match', models.ForeignKey(help_text='The game these statistics are for', on_delete=django.db.models.deletion.CASCADE, related_name='stats', to='games.game')),
                ('player', models.ForeignKey(help_text='The player these statistics belong to', on_delete=django.db.models.deletion.CASCADE, related_name='match_stats', to='players.player')),
            ],
            options={
                'verbose_name': 'Match Statistics',
                'verbose_name_plural': 'Match Statistics',
            },
        ),
        migrations.CreateModel(
            name='Ticket',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('purchase_date', models.DateTimeField(auto_now_add=True, db_index=True, help_text='When the ticket was purchased')),
                ('ticket_code', models.CharField(db_index=True, help_text='Unique code to identify this ticket', max_length=20, unique=True)),
                ('is_used', models.BooleanField(default=False, help_text='Whether the ticket has been used to enter the venue')),
                ('payment_id', models.CharField(help_text='ID of the payment transaction for this ticket', max_length=100)),
                ('match', models.ForeignKey(help_text='The game this ticket is for', on_delete=django.db.models.deletion.CASCADE, related_name='tickets', to='games.game')),
                ('viewer', models.ForeignKey(help_text='The user who purchased this ticket', on_delete=django.db.models.deletion.CASCADE, related_name='tickets', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Ticket',
                'verbose_name_plural': 'Tickets',
            },
        ),
        migrations.AddIndex(
            model_name='game',
            index=models.Index(fields=['status', 'date_time'], name='games_game_status_02be33_idx'),
        ),
        migrations.AddIndex(
            model_name='game',
            index=models.Index(fields=['league', 'status'], name='games_game_league__fa0241_idx'),
        ),
        migrations.AddIndex(
            model_name='game',
            index=models.Index(fields=['home_team', 'away_team'], name='games_game_home_te_c15004_idx'),
        ),
        migrations.AddIndex(
            model_name='matchstats',
            index=models.Index(fields=['match'], name='games_match_match_i_9897aa_idx'),
        ),
        migrations.AddIndex(
            model_name='matchstats',
            index=models.Index(fields=['player'], name='games_match_player__0dd227_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='matchstats',
            unique_together={('match', 'player')},
        ),
        migrations.AddIndex(
            model_name='ticket',
            index=models.Index(fields=['viewer', 'match'], name='games_ticke_viewer__03c65d_idx'),
        ),
        migrations.AddIndex(
            model_name='ticket',
            index=models.Index(fields=['match', 'is_used'], name='games_ticke_match_i_13efa5_idx'),
        ),
    ]
