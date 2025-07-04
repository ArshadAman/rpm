from django.urls import path
from . import views

app_name = 'calling_agent'

urlpatterns = [
    # Call Schedule Management
    path('', views.call_schedule_list, name='call_schedule_list'),
    path('schedules/', views.call_schedule_list, name='call_schedule_list'),
    path('schedules/create/', views.create_call_schedule, name='create_call_schedule'),
    path('schedules/<uuid:schedule_id>/edit/', views.edit_call_schedule, name='edit_call_schedule'),
    path('schedules/<uuid:schedule_id>/delete/', views.delete_call_schedule, name='delete_call_schedule'),
    
    # Call Sessions
    path('upcoming/', views.upcoming_calls, name='upcoming_calls'),
    path('debug/', views.debug_calls, name='debug_calls'),
    path('test-call/', views.test_call_creation, name='test_call_creation'),
    path('history/', views.call_history, name='call_history'),
    path('calls/<uuid:call_session_id>/', views.call_details, name='call_details'),
    path('calls/<uuid:call_session_id>/initiate/', views.initiate_call, name='initiate_call'),
    
    # Twilio Webhooks (no authentication required)
    path('api/webhook/<uuid:call_session_id>/', views.twilio_webhook, name='twilio_webhook'),
    path('api/status/<uuid:call_session_id>/', views.twilio_status_callback, name='twilio_status_callback'),
    
    # API Endpoints
    path('api/trigger-scheduling/', views.trigger_weekly_scheduling, name='trigger_weekly_scheduling'),
]
