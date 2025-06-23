from django.contrib import admin
from .models import VoiceInteraction, VoiceQuestion, VoiceCallSchedule, AIKnowledgeBase

@admin.register(VoiceInteraction)
class VoiceInteractionAdmin(admin.ModelAdmin):
    list_display = [
        'patient', 'interaction_type', 'call_status', 
        'created_at', 'call_duration', 'follow_up_required'
    ]
    list_filter = [
        'interaction_type', 'call_status', 'follow_up_required', 
        'created_at'
    ]
    search_fields = ['patient__user__first_name', 'patient__user__last_name', 'phone_number']
    readonly_fields = ['twilio_call_sid', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('patient', 'interaction_type', 'call_status', 'phone_number')
        }),
        ('Call Details', {
            'fields': ('twilio_call_sid', 'call_duration', 'call_recording_url')
        }),
        ('Conversation Data', {
            'fields': ('questions_asked', 'patient_responses', 'ai_responses', 'transcript'),
            'classes': ('collapse',)
        }),
        ('Analysis', {
            'fields': ('sentiment_score', 'health_alerts', 'follow_up_required'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('scheduled_time', 'started_at', 'ended_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(VoiceQuestion)
class VoiceQuestionAdmin(admin.ModelAdmin):
    list_display = ['question_type', 'question_text', 'priority', 'is_active', 'condition_required']
    list_filter = ['question_type', 'is_active', 'priority']
    search_fields = ['question_text', 'condition_required']
    ordering = ['priority', 'question_type']

@admin.register(VoiceCallSchedule)
class VoiceCallScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'patient', 'frequency', 'preferred_time', 'is_active', 
        'next_call_scheduled', 'last_call_completed'
    ]
    list_filter = ['frequency', 'is_active', 'timezone']
    search_fields = ['patient__user__first_name', 'patient__user__last_name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(AIKnowledgeBase)
class AIKnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ['knowledge_type', 'title', 'is_active', 'created_at']
    list_filter = ['knowledge_type', 'is_active']
    search_fields = ['title', 'content', 'keywords']
    readonly_fields = ['embedding_vector', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('knowledge_type', 'title', 'is_active')
        }),
        ('Content', {
            'fields': ('content', 'keywords')
        }),
        ('Technical', {
            'fields': ('embedding_vector',),
            'classes': ('collapse',)
        })
    )
