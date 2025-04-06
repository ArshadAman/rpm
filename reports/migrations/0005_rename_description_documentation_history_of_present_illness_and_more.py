# Generated by Django 5.1 on 2025-04-06 10:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0004_rename_cheif_complaint_documentation_chief_complaint_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='documentation',
            old_name='description',
            new_name='history_of_present_illness',
        ),
        migrations.AlterField(
            model_name='documentation',
            name='subjective',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='documentation',
            name='title',
            field=models.CharField(choices=[('RPM Progress Note', 'RPM Progress Note'), ('Progress Note', 'Progress Note')], default='Progress Note', max_length=255),
        ),
    ]
