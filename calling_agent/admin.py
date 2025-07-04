from django.contrib import admin
from django.utils import timezone
from .models import (
    CallSchedule, 
    CallQuestionTemplate, 
    CallSession, 
    CallResponse, 
    CallAlert, 
    CallConfiguration
)


@admin.register(CallSchedule)
class CallScheduleAdmin(admin.ModelAdmin):
    list_display = ['patient', 'get_patient_email', 'frequency', 'preferred_day_display', 'preferred_time', 'is_active', 'created_at']
    list_filter = ['frequency', 'preferred_day', 'is_active', 'created_at']
    search_fields = ['patient__user__email', 'patient__user__first_name', 'patient__user__last_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    def get_patient_email(self, obj):
        return obj.patient.user.email
    get_patient_email.short_description = 'Patient Email'
    
    def preferred_day_display(self, obj):
        return obj.get_preferred_day_display()
    preferred_day_display.short_description = 'Preferred Day'


@admin.register(CallQuestionTemplate)
class CallQuestionTemplateAdmin(admin.ModelAdmin):
    list_display = ['order', 'question_text_short', 'question_type', 'priority', 'is_required', 'is_active']
    list_filter = ['question_type', 'priority', 'is_required', 'is_active']
    search_fields = ['question_text']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['order', 'priority']
    
    def question_text_short(self, obj):
        return obj.question_text[:60] + '...' if len(obj.question_text) > 60 else obj.question_text
    question_text_short.short_description = 'Question'


@admin.register(CallSession)
class CallSessionAdmin(admin.ModelAdmin):
    list_display = ['scheduled_time', 'patient', 'get_patient_email', 'status', 'call_duration', 'retry_count']
    list_filter = ['status', 'scheduled_time', 'call_schedule__frequency']
    search_fields = ['patient__user__email', 'patient__user__first_name', 'patient__user__last_name', 'call_sid']
    readonly_fields = ['id', 'created_at', 'updated_at', 'duration_minutes']
    date_hierarchy = 'scheduled_time'
    
    def get_patient_email(self, obj):
        return obj.patient.user.email
    get_patient_email.short_description = 'Patient Email'


@admin.register(CallResponse)
class CallResponseAdmin(admin.ModelAdmin):
    list_display = ['call_session', 'question_short', 'processed_response_short', 'numeric_value', 'is_concerning', 'confidence_score']
    list_filter = ['is_concerning', 'requires_followup', 'question__priority', 'timestamp']
    search_fields = ['response_text', 'processed_response', 'call_session__patient__user__email']
    readonly_fields = ['id', 'timestamp']
    
    def question_short(self, obj):
        return obj.question.question_text[:40] + '...' if len(obj.question.question_text) > 40 else obj.question.question_text
    question_short.short_description = 'Question'
    
    def processed_response_short(self, obj):
        if obj.processed_response:
            return obj.processed_response[:50] + '...' if len(obj.processed_response) > 50 else obj.processed_response
        return obj.response_text[:50] + '...' if len(obj.response_text) > 50 else obj.response_text
    processed_response_short.short_description = 'Response'


@admin.register(CallAlert)
class CallAlertAdmin(admin.ModelAdmin):
    list_display = ['title', 'patient', 'alert_type', 'severity', 'is_resolved', 'created_at']
    list_filter = ['alert_type', 'severity', 'is_resolved', 'created_at']
    search_fields = ['title', 'description', 'patient__user__email']
    readonly_fields = ['id', 'created_at']
    actions = ['mark_resolved']
    
    def mark_resolved(self, request, queryset):
        queryset.update(is_resolved=True, resolved_by=request.user, resolved_at=timezone.now())
    mark_resolved.short_description = "Mark selected alerts as resolved"


@admin.register(CallConfiguration)
class CallConfigurationAdmin(admin.ModelAdmin):
    list_display = ['name', 'max_call_duration', 'ai_model', 'enable_recording', 'is_active']
    list_filter = ['is_active', 'enable_recording']
    readonly_fields = ['id', 'created_at', 'updated_at']
