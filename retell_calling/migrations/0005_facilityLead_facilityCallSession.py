# Generated migration for FacilityLead models

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('retell_calling', '0004_bulkcallsession_leadcallsession_bulk_session_id'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='FacilityLead',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('facility_name', models.CharField(help_text='Name of the facility', max_length=255)),
                ('category', models.CharField(blank=True, help_text='Facility category (e.g., General, Low Income)', max_length=100, null=True)),
                ('phone_number', models.CharField(help_text='Primary phone number', max_length=20)),
                ('address', models.TextField(help_text='Street address')),
                ('city', models.CharField(help_text='City', max_length=100)),
                ('zip_code', models.CharField(help_text='ZIP code', max_length=10)),
                ('capacity', models.PositiveIntegerField(blank=True, help_text='Facility capacity', null=True)),
                ('hospice', models.CharField(blank=True, choices=[('Y', 'Yes'), ('N', 'No')], help_text='Provides hospice services', max_length=10, null=True)),
                ('non_ambulatory', models.CharField(blank=True, choices=[('Y', 'Yes'), ('N', 'No')], help_text='Serves non-ambulatory patients', max_length=10, null=True)),
                ('call_attempted', models.BooleanField(default=False, help_text='Whether a call has been attempted')),
                ('call_completed', models.BooleanField(default=False, help_text='Whether the call was completed')),
                ('email_sent', models.BooleanField(default=False, help_text='Whether follow-up email has been sent')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('uploaded_by', models.ForeignKey(blank=True, help_text='Admin who uploaded this facility', null=True, on_delete=django.db.models.deletion.SET_NULL, to='auth.user')),
            ],
            options={
                'verbose_name': 'Facility Lead',
                'verbose_name_plural': 'Facility Leads',
                'ordering': ['facility_name'],
                'unique_together': {('facility_name', 'phone_number', 'city')},
            },
        ),
        migrations.CreateModel(
            name='FacilityCallSession',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('bulk_session_id', models.UUIDField(blank=True, help_text='Associated bulk calling session', null=True)),
                ('retell_call_id', models.CharField(help_text='Unique call ID from Retell API', max_length=100, unique=True)),
                ('call_status', models.CharField(choices=[('initiated', 'Initiated'), ('ringing', 'Ringing'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('failed', 'Failed'), ('no_answer', 'No Answer'), ('busy', 'Busy'), ('cancelled', 'Cancelled')], default='initiated', max_length=20)),
                ('from_number', models.CharField(help_text='Phone number used to make the call', max_length=20)),
                ('to_number', models.CharField(help_text="Facility's phone number", max_length=20)),
                ('start_timestamp', models.BigIntegerField(blank=True, help_text='Call start time as Unix timestamp', null=True)),
                ('end_timestamp', models.BigIntegerField(blank=True, help_text='Call end time as Unix timestamp', null=True)),
                ('duration_ms', models.IntegerField(blank=True, help_text='Call duration in milliseconds', null=True)),
                ('transcript', models.TextField(blank=True, help_text='Full call transcript from Retell')),
                ('transcript_object', models.JSONField(blank=True, help_text='Structured transcript object from Retell', null=True)),
                ('recording_url', models.URLField(blank=True, help_text='URL to call recording')),
                ('agent_id', models.CharField(blank=True, help_text='Retell agent ID used for the call', max_length=100)),
                ('disconnection_reason', models.CharField(blank=True, help_text='Reason for call disconnection', max_length=50)),
                ('ai_summary', models.JSONField(blank=True, help_text='AI-generated summary and analysis', null=True)),
                ('call_analysis', models.JSONField(blank=True, help_text="Retell's call analysis data", null=True)),
                ('email_sent', models.BooleanField(default=False, help_text='Whether follow-up email has been sent')),
                ('email_sent_at', models.DateTimeField(blank=True, help_text='When the email was sent', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('facility', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='call_sessions', to='retell_calling.facilitylead')),
            ],
            options={
                'verbose_name': 'Facility Call Session',
                'verbose_name_plural': 'Facility Call Sessions',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='FacilityCallSummary',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('summary_text', models.TextField(help_text='AI-generated summary of the call')),
                ('key_points', models.JSONField(default=list, help_text='List of key discussion points from the call')),
                ('concerning_flags', models.JSONField(default=list, help_text='List of concerning responses or red flags identified')),
                ('health_metrics', models.JSONField(default=dict, help_text='Structured data extracted from the call')),
                ('ai_confidence_score', models.DecimalField(blank=True, decimal_places=2, help_text='AI confidence score for the summary (0.00-1.00)', max_digits=3, null=True)),
                ('generated_at', models.DateTimeField(auto_now_add=True)),
                ('call_session', models.OneToOneField(help_text='Associated facility call session', on_delete=django.db.models.deletion.CASCADE, related_name='summary', to='retell_calling.facilitycallsession')),
                ('facility', models.ForeignKey(help_text='Facility associated with this summary', on_delete=django.db.models.deletion.CASCADE, related_name='call_summaries', to='retell_calling.facilitylead')),
            ],
            options={
                'verbose_name': 'Facility Call Summary',
                'verbose_name_plural': 'Facility Call Summaries',
                'ordering': ['-generated_at'],
            },
        ),
    ]
