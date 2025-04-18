# Generated by Django 5.1 on 2024-12-27 21:17

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Documentation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('cheif_complaint', models.TextField(blank=True, max_length=255, null=True)),
                ('subjective', models.TextField(blank=True, max_length=255, null=True)),
                ('objective', models.TextField(blank=True, max_length=255, null=True)),
                ('assessment', models.TextField(blank=True, max_length=255, null=True)),
                ('plan', models.TextField(blank=True, max_length=255, null=True)),
                ('file', models.FileField(upload_to='documentations/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('report', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documentations', to='reports.reports')),
            ],
        ),
    ]
