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
    
    # Lead Call Management
    path('trigger-lead-call/', views.trigger_lead_call, name='trigger_lead_call'),
    path('trigger-bulk-lead-calls/', views.trigger_bulk_lead_calls, name='trigger_bulk_lead_calls'),
    path('bulk-call-status/<uuid:bulk_session_id>/', views.bulk_call_status, name='bulk_call_status'),
    path('pause-bulk-calling/<uuid:bulk_session_id>/', views.pause_bulk_calling, name='pause_bulk_calling'),
    path('resume-bulk-calling/<uuid:bulk_session_id>/', views.resume_bulk_calling, name='resume_bulk_calling'),
    path('debug-bulk-calling/', views.debug_bulk_calling, name='debug_bulk_calling'),
    path('test-summary-generation/', views.test_summary_generation, name='test_summary_generation'),
    path('leads-call-summaries/', views.leads_call_summaries_list, name='leads_call_summaries_list'),
    path('lead/<int:lead_id>/call-summaries/', views.lead_call_summaries, name='lead_call_summaries'),
]
