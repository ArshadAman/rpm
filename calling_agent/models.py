from django.db import models
from django.contrib.auth.models import User
from rpm_users.models import Patient
import uuid
from django.utils import timezone


class CallSchedule(models.Model):
    """Model to manage weekly call schedules for patients"""
    FREQUENCY_CHOICES = [
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-weekly'),
        ('monthly', 'Monthly'),
    ]
    
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='call_schedules')
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='weekly')
    preferred_day = models.IntegerField(choices=DAY_CHOICES, default=1)  # Default Tuesday
    preferred_time = models.TimeField(help_text="Preferred time for calls in patient's timezone")
    is_active = models.BooleanField(default=True)
    timezone = models.CharField(max_length=50, default='UTC')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['patient', 'frequency']
    
    def __str__(self):
        return f"{self.patient.user.email} - {self.get_frequency_display()} on {self.get_preferred_day_display()}"


class CallQuestionTemplate(models.Model):
    """Template for questions to ask during calls"""
    QUESTION_TYPES = [
        ('scale', 'Scale (1-10)'),
        ('yes_no', 'Yes/No'),
        ('multiple_choice', 'Multiple Choice'),
        ('open_ended', 'Open Ended'),
        ('numeric', 'Numeric Value'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    question_text = models.TextField(help_text="The question to ask the patient")
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    options = models.JSONField(null=True, blank=True, help_text="For multiple choice questions, store options as JSON array")
    order = models.PositiveIntegerField(default=0, help_text="Order in which to ask questions")
    is_required = models.BooleanField(default=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    follow_up_conditions = models.JSONField(null=True, blank=True, help_text="Conditions that trigger follow-up questions")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'priority']
    
    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}..."


class CallSession(models.Model):
    """Model to track individual call sessions"""
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('no_answer', 'No Answer'),
        ('busy', 'Busy'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='call_sessions')
    call_schedule = models.ForeignKey(CallSchedule, on_delete=models.CASCADE, related_name='call_sessions')
    scheduled_time = models.DateTimeField()
    actual_start_time = models.DateTimeField(null=True, blank=True)
    actual_end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    call_duration = models.DurationField(null=True, blank=True)
    call_sid = models.CharField(max_length=100, null=True, blank=True, help_text="Twilio Call SID")
    recording_url = models.URLField(null=True, blank=True)
    notes = models.TextField(blank=True, help_text="Additional notes from the call")
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-scheduled_time']
    
    def __str__(self):
        return f"Call to {self.patient.user.email} on {self.scheduled_time.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def duration_minutes(self):
        if self.call_duration:
            return self.call_duration.total_seconds() / 60
        return 0


class CallResponse(models.Model):
    """Model to store patient responses during calls"""
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    call_session = models.ForeignKey(CallSession, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(CallQuestionTemplate, on_delete=models.CASCADE)
    response_text = models.TextField(help_text="Raw response from patient")
    processed_response = models.TextField(null=True, blank=True, help_text="AI-processed/cleaned response")
    numeric_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    confidence_score = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True, help_text="AI confidence in response understanding (0-1)")
    is_concerning = models.BooleanField(default=False, help_text="Flagged as concerning by AI")
    requires_followup = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['call_session', 'question']
    
    def __str__(self):
        return f"Response to '{self.question.question_text[:30]}...' in {self.call_session}"


class CallAlert(models.Model):
    """Model to track alerts generated from call responses"""
    ALERT_TYPES = [
        ('critical_response', 'Critical Response'),
        ('missed_call', 'Missed Call'),
        ('concerning_trend', 'Concerning Trend'),
        ('technical_failure', 'Technical Failure'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    call_session = models.ForeignKey(CallSession, on_delete=models.CASCADE, related_name='alerts', null=True, blank=True)
    call_response = models.ForeignKey(CallResponse, on_delete=models.CASCADE, related_name='alerts', null=True, blank=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='call_alerts')
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS)
    title = models.CharField(max_length=200)
    description = models.TextField()
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_call_alerts')
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at', '-severity']
    
    def __str__(self):
        return f"{self.get_severity_display()} Alert: {self.title}"


class CallConfiguration(models.Model):
    """Global configuration for the calling system"""
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    name = models.CharField(max_length=100, unique=True)
    max_call_duration = models.DurationField(default=timezone.timedelta(minutes=15))
    max_daily_retries = models.PositiveIntegerField(default=3)
    ai_model = models.CharField(max_length=50, default='gpt-3.5-turbo')
    voice_model = models.CharField(max_length=50, default='tts-1')
    enable_recording = models.BooleanField(default=True)
    emergency_keywords = models.JSONField(default=list, help_text="Keywords that trigger immediate alerts")
    business_hours_start = models.TimeField(default='09:00')
    business_hours_end = models.TimeField(default='17:00')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
