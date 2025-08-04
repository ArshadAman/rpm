from django.db import models
import uuid
from rpm_users.models import Patient


class RetellCallSession(models.Model):
    """Extended call session for Retell AI integration"""
    
    RETELL_STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('ringing', 'Ringing'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('no_answer', 'No Answer'),
        ('busy', 'Busy'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='retell_call_sessions')
    retell_call_id = models.CharField(max_length=100, unique=True, help_text="Unique call ID from Retell API")
    call_status = models.CharField(max_length=20, choices=RETELL_STATUS_CHOICES, default='initiated')
    from_number = models.CharField(max_length=20, help_text="Phone number used to make the call")
    to_number = models.CharField(max_length=20, help_text="Patient's phone number")
    start_timestamp = models.BigIntegerField(null=True, blank=True, help_text="Call start time as Unix timestamp")
    end_timestamp = models.BigIntegerField(null=True, blank=True, help_text="Call end time as Unix timestamp")
    duration_ms = models.IntegerField(null=True, blank=True, help_text="Call duration in milliseconds")
    transcript = models.TextField(blank=True, help_text="Full call transcript from Retell")
    transcript_object = models.JSONField(null=True, blank=True, help_text="Structured transcript object from Retell")
    recording_url = models.URLField(blank=True, help_text="URL to call recording")
    agent_id = models.CharField(max_length=100, blank=True, help_text="Retell agent ID used for the call")
    disconnection_reason = models.CharField(max_length=50, blank=True, help_text="Reason for call disconnection")
    ai_summary = models.JSONField(null=True, blank=True, help_text="AI-generated summary and analysis")
    call_analysis = models.JSONField(null=True, blank=True, help_text="Retell's call analysis data")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Retell Call Session"
        verbose_name_plural = "Retell Call Sessions"
    
    def __str__(self):
        return f"Retell Call to {self.patient.user.email} - {self.call_status}"
    
    @property
    def duration_seconds(self):
        """Convert duration from milliseconds to seconds"""
        if self.duration_ms:
            return self.duration_ms / 1000
        return 0
    
    @property
    def duration_minutes(self):
        """Convert duration from milliseconds to minutes"""
        if self.duration_ms:
            return self.duration_ms / (1000 * 60)
        return 0


class CallSummary(models.Model):
    """AI-generated summaries of call transcripts"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    call_session = models.OneToOneField(
        RetellCallSession, 
        on_delete=models.CASCADE, 
        related_name='summary',
        help_text="Associated call session"
    )
    patient = models.ForeignKey(
        Patient, 
        on_delete=models.CASCADE, 
        related_name='call_summaries',
        help_text="Patient associated with this summary"
    )
    summary_text = models.TextField(help_text="AI-generated summary of the call")
    key_points = models.JSONField(
        default=list, 
        help_text="List of key discussion points from the call"
    )
    concerning_flags = models.JSONField(
        default=list, 
        help_text="List of concerning responses or red flags identified"
    )
    health_metrics = models.JSONField(
        default=dict, 
        help_text="Structured health data extracted from the call"
    )
    ai_confidence_score = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="AI confidence score for the summary (0.00-1.00)"
    )
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-generated_at']
        verbose_name = "Call Summary"
        verbose_name_plural = "Call Summaries"
    
    def __str__(self):
        return f"Summary for {self.patient.user.email} - {self.generated_at.strftime('%Y-%m-%d %H:%M')}"


class CallCondition(models.Model):
    """Configurable conditions for triggering calls"""
    
    CONDITION_TYPE_CHOICES = [
        ('time_based', 'Time Based'),
        ('health_metric', 'Health Metric'),
        ('missed_reading', 'Missed Reading'),
        ('alert_triggered', 'Alert Triggered'),
        ('manual', 'Manual Trigger'),
        ('follow_up', 'Follow Up'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, help_text="Descriptive name for the condition")
    condition_type = models.CharField(
        max_length=50, 
        choices=CONDITION_TYPE_CHOICES,
        help_text="Type of condition that triggers calls"
    )
    parameters = models.JSONField(
        default=dict, 
        help_text="Configuration parameters for the condition (JSON format)"
    )
    is_active = models.BooleanField(
        default=True, 
        help_text="Whether this condition is currently active"
    )
    description = models.TextField(
        blank=True, 
        help_text="Detailed description of when this condition triggers"
    )
    priority = models.PositiveIntegerField(
        default=1, 
        help_text="Priority level for condition evaluation (1=highest)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['priority', 'name']
        verbose_name = "Call Condition"
        verbose_name_plural = "Call Conditions"
    
    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"{self.name} ({self.get_condition_type_display()}) - {status}"
