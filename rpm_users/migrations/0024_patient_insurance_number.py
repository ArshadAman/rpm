# Generated by Django 5.2.1 on 2025-05-27 05:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rpm_users', '0023_remove_interestlead_can_follow_instructions_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='patient',
            name='insurance_number',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
