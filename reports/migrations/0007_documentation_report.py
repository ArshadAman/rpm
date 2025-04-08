# Generated by Django 5.1 on 2025-04-08 16:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0006_remove_documentation_report_documentation_patient'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentation',
            name='report',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='documentations', to='reports.reports'),
        ),
    ]
