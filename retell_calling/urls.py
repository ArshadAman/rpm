from django.urls import path
from . import views

app_name = 'retell_calling'

urlpatterns = [
    # Call Management
    path('trigger-call/', views.trigger_call, name='trigger_call'),
    path('patients/', views.list_patients, name='list_patients'),
    path('call-status/<int:call_session_id>/', views.call_status, name='call_status'),
    
    # Webhook and Transcript Processing
    path('webhook/', views.retell_webhook, name='retell_webhook'),
    path('transcript/<int:call_session_id>/', views.call_transcript, name='call_transcript'),
    path('process-transcript/<int:call_session_id>/', views.process_transcript, name='process_transcript'),
    
    # Call Summaries Management
    path('call-summaries/', views.call_summaries_list, name='call_summaries_list'),
    path('patient/<uuid:patient_id>/call-summaries/', views.patient_call_summaries, name='patient_call_summaries'),
    path('debug/call-summaries/', views.debug_call_summaries, name='debug_call_summaries'),
]
