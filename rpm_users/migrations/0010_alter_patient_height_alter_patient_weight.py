# Generated by Django 5.1 on 2024-10-11 21:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rpm_users', '0009_patient_bmi_alter_patient_height_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='patient',
            name='height',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='patient',
            name='weight',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]
