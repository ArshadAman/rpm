from django.db import models
from rpm_users.models import Patient
from django.contrib.auth.models import User

class VoiceInteraction(models.Model):
    INTERACTION_TYPES = [
        ('outbound_scheduled', 'Outbound Scheduled Call'),
        ('inbound_patient', 'Inbound Patient Call'),
        ('emergency_check', 'Emergency Check Call'),
    ]
    
    CALL_STATUS = [
        ('initiated', 'Call Initiated'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('no_answer', 'No Answer'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='voice_interactions')
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES, default='outbound_scheduled')
    call_status = models.CharField(max_length=15, choices=CALL_STATUS, default='initiated')
    
    # Call details
    twilio_call_sid = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=20)
    call_duration = models.DurationField(blank=True, null=True)
    
    # Interaction content
    questions_asked = models.JSONField(default=list)  # List of questions asked
    patient_responses = models.JSONField(default=list)  # Patient's responses
    ai_responses = models.JSONField(default=list)  # AI generated responses
    
    # Audio recordings
    call_recording_url = models.URLField(blank=True, null=True)
    transcript = models.TextField(blank=True, null=True)
    
    # Timestamps
    scheduled_time = models.DateTimeField(blank=True, null=True)
    started_at = models.DateTimeField(blank=True, null=True)
    ended_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Analysis
    sentiment_score = models.FloatField(blank=True, null=True)  # -1 to 1
    health_alerts = models.JSONField(default=list)  # Any health concerns detected
    follow_up_required = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Voice Interaction - {self.patient.user.get_full_name()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

class VoiceQuestion(models.Model):
    QUESTION_TYPES = [
        ('health_check', 'General Health Check'),
        ('symptom_inquiry', 'Symptom Inquiry'),
        ('medication_adherence', 'Medication Adherence'),
        ('vital_signs', 'Vital Signs'),
        ('emergency_assessment', 'Emergency Assessment'),
        ('satisfaction', 'Satisfaction Survey'),
    ]
    
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    question_text = models.TextField()
    expected_response_type = models.CharField(max_length=50)  # 'yes_no', 'scale_1_10', 'open_text', etc.
    priority = models.IntegerField(default=1)  # 1 = highest priority
    is_active = models.BooleanField(default=True)
    
    # Condition-based questions
    condition_required = models.CharField(max_length=100, blank=True, null=True)  # e.g., 'hypertension'
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['priority', 'question_type']
        
    def __str__(self):
        return f"{self.get_question_type_display()}: {self.question_text[:50]}..."

class VoiceCallSchedule(models.Model):
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('bi_weekly', 'Bi-Weekly'),
        ('monthly', 'Monthly'),
        ('custom', 'Custom'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='call_schedules')
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default='weekly')
    preferred_time = models.TimeField()  # Preferred time of day
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Custom scheduling
    custom_schedule = models.JSONField(blank=True, null=True)  # For complex schedules
    
    # Status
    is_active = models.BooleanField(default=True)
    next_call_scheduled = models.DateTimeField(blank=True, null=True)
    last_call_completed = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Call Schedule - {self.patient.user.get_full_name()} - {self.frequency}"

class AIKnowledgeBase(models.Model):
    KNOWLEDGE_TYPES = [
        ('rpm_general', 'RPM General Information'),
        ('medical_conditions', 'Medical Conditions'),
        ('emergency_protocols', 'Emergency Protocols'),
        ('medication_info', 'Medication Information'),
        ('faq', 'Frequently Asked Questions'),
    ]
    
    knowledge_type = models.CharField(max_length=20, choices=KNOWLEDGE_TYPES)
    title = models.CharField(max_length=200)
    content = models.TextField()
    keywords = models.JSONField(default=list)  # For semantic search
    
    # Vector embeddings for RAG
    embedding_vector = models.JSONField(blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['knowledge_type', 'title']
        
    def __str__(self):
        return f"{self.get_knowledge_type_display()}: {self.title}"
