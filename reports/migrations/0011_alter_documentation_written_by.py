# Generated by Django 5.2.1 on 2025-05-28 06:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0010_documentation_written_by'),
    ]

    operations = [
        migrations.AlterField(
            model_name='documentation',
            name='written_by',
            field=models.TextField(blank=True, max_length=255, null=True),
        ),
    ]
