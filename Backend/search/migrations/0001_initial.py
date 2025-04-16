# Generated by Django 5.1.8 on 2025-04-16 11:56

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SearchIndex',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_type', models.CharField(choices=[('player', 'Player'), ('team', 'Team'), ('game', 'Game'), ('news', 'News')], max_length=20)),
                ('object_id', models.PositiveIntegerField()),
                ('indexed_at', models.DateTimeField(auto_now=True)),
                ('is_indexed', models.BooleanField(default=False)),
            ],
            options={
                'indexes': [models.Index(fields=['object_type', 'is_indexed'], name='search_sear_object__4a6db9_idx')],
                'unique_together': {('object_type', 'object_id')},
            },
        ),
        migrations.CreateModel(
            name='SearchQuery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('query', models.CharField(max_length=255)),
                ('results_count', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True, null=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'indexes': [models.Index(fields=['-created_at'], name='search_sear_created_29f94e_idx'), models.Index(fields=['query'], name='search_sear_query_eedf16_idx')],
            },
        ),
    ]
