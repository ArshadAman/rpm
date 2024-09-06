# Generated by Django 5.1 on 2024-09-04 08:37

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Moderator',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(blank=True, max_length=255, null=True)),
                ('first_name', models.CharField(blank=True, max_length=255, null=True)),
                ('last_name', models.CharField(blank=True, max_length=255, null=True)),
                ('date_of_birth', models.DateField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Patient',
            fields=[
                ('email', models.EmailField(blank=True, max_length=255, null=True)),
                ('first_name', models.CharField(blank=True, max_length=255, null=True)),
                ('last_name', models.CharField(blank=True, max_length=255, null=True)),
                ('date_of_birth', models.DateField(blank=True, null=True)),
                ('height', models.IntegerField(blank=True, null=True)),
                ('wight', models.IntegerField(blank=True, null=True)),
                ('insurance', models.IntegerField(blank=True, null=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('moderator_assigned', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='rpm_users.moderator')),
            ],
        ),
    ]
