from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ("reports", "0011_alter_documentation_written_by"),
    ]

    operations = [
        migrations.AddField(
            model_name="documentation",
            name="patient_name",
            field=models.CharField(max_length=255, blank=True, null=True),
        ),
        migrations.AddField(
            model_name="documentation",
            name="patient_date_of_birth",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="documentation",
            name="patient_sex",
            field=models.CharField(max_length=10, blank=True, null=True),
        ),
        migrations.AddField(
            model_name="documentation",
            name="patient_monitoring_parameters",
            field=models.CharField(max_length=255, blank=True, null=True),
        ),
        migrations.AddField(
            model_name="documentation",
            name="patient_clinical_staff",
            field=models.CharField(max_length=255, blank=True, null=True),
        ),
        migrations.AddField(
            model_name="documentation",
            name="patient_moderator",
            field=models.CharField(max_length=255, blank=True, null=True),
        ),
        migrations.AddField(
            model_name="documentation",
            name="patient_report_date",
            field=models.DateField(blank=True, null=True),
        ),
    ]
