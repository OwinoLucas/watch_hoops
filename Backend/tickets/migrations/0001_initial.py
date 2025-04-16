# Generated by Django 5.1.8 on 2025-04-16 09:44

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('games', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TicketPurchase',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('ticket_type', models.CharField(choices=[('STANDARD', 'Standard'), ('VIP', 'VIP'), ('COURTSIDE', 'Courtside')], max_length=20)),
                ('quantity', models.PositiveIntegerField()),
                ('total_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('purchase_date', models.DateTimeField(auto_now_add=True)),
                ('payment_status', models.CharField(default='PENDING', max_length=20)),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ticket_sales', to='games.game')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ticket_purchases', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-purchase_date'],
            },
        ),
        migrations.CreateModel(
            name='Ticket',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('ticket_type', models.CharField(choices=[('STANDARD', 'Standard'), ('VIP', 'VIP'), ('COURTSIDE', 'Courtside')], max_length=20)),
                ('status', models.CharField(choices=[('ACTIVE', 'Active'), ('USED', 'Used'), ('EXPIRED', 'Expired'), ('CANCELLED', 'Cancelled')], default='ACTIVE', max_length=20)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('purchase_date', models.DateTimeField(auto_now_add=True)),
                ('validation_date', models.DateTimeField(blank=True, null=True)),
                ('seat_info', models.JSONField(blank=True, null=True)),
                ('qr_code', models.ImageField(blank=True, null=True, upload_to='tickets/qr_codes/')),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='game_tickets', to='games.game')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='purchased_tickets', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-purchase_date'],
                'indexes': [models.Index(fields=['user', 'status'], name='tickets_tic_user_id_ee01b8_idx'), models.Index(fields=['game', 'ticket_type'], name='tickets_tic_game_id_dddb81_idx')],
            },
        ),
    ]
