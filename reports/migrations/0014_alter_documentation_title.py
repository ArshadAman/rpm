# Generated by Django 5.2.3 on 2025-06-11 20:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0013_rename_patient_clinical_staff_documentation_doc_clinical_staff_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='documentation',
            name='title',
            field=models.CharField(choices=[('RPM Progress Note', 'RPM Progress Note'), ('CCN-HTN Progress Note', 'CCN-HTN Progress Note'), ('Progress Note', 'Progress Note')], default='Progress Note', max_length=255),
        ),
    ]
