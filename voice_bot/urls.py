from django.urls import path
from . import views
from .twilio_service import handle_call, process_speech, call_status_callback

urlpatterns = [
    # Voice bot management views
    path('dashboard/', views.voice_bot_dashboard, name='voice_bot_dashboard'),
    path('schedule/<int:patient_id>/', views.schedule_voice_calls, name='schedule_voice_calls'),
    path('interactions/<int:patient_id>/', views.patient_voice_interactions, name='patient_voice_interactions'),
    path('interaction/<int:interaction_id>/', views.voice_interaction_detail, name='voice_interaction_detail'),
    
    # Manual call initiation
    path('initiate-call/<int:patient_id>/', views.initiate_manual_call, name='initiate_manual_call'),
    
    # Twilio webhooks
    path('handle-call/<int:interaction_id>/', handle_call, name='handle_call'),
    path('process-speech/', process_speech, name='process_speech'),
    path('call-status/<int:interaction_id>/', call_status_callback, name='call_status_callback'),
    
    # API endpoints
    path('api/patient-summary/<int:patient_id>/', views.patient_voice_summary, name='patient_voice_summary'),
    path('api/emergency-alert/', views.create_emergency_alert, name='create_emergency_alert'),
]
