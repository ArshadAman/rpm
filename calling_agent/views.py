from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import datetime, timedelta
import json

from rpm_users.models import Patient
from .models import CallSchedule, CallSession, CallQuestionTemplate
from .twilio_service import TwilioCallService


def is_staff_or_admin(user):
    """Check if user is staff or admin"""
    return user.is_staff or user.is_superuser


@login_required
@user_passes_test(is_staff_or_admin)
def call_schedule_list(request):
    """List all call schedules"""
    schedules = CallSchedule.objects.select_related('patient__user').filter(is_active=True)
    context = {
        'schedules': schedules,
        'title': 'Call Schedules'
    }
    return render(request, 'calling_agent/schedule_list.html', context)


@login_required
@user_passes_test(is_staff_or_admin)
def create_call_schedule(request):
    """Create a new call schedule for a patient"""
    if request.method == 'POST':
        try:
            patient_id = request.POST.get('patient')
            frequency = request.POST.get('frequency', 'weekly')
            preferred_day = int(request.POST.get('preferred_day', 1))
            preferred_time = request.POST.get('preferred_time')
            timezone_str = request.POST.get('timezone', 'UTC')
            
            # Get patient
            patient = get_object_or_404(Patient, id=patient_id)
            
            # Check if schedule already exists (active or inactive)
            existing_schedule = CallSchedule.objects.filter(
                patient=patient, 
                frequency=frequency
            ).first()
            
            if existing_schedule:
                if existing_schedule.is_active:
                    messages.error(request, f'An active {frequency} call schedule already exists for this patient.')
                    return redirect('calling_agent:create_call_schedule')
                else:
                    # Reactivate the existing inactive schedule
                    existing_schedule.preferred_day = preferred_day
                    existing_schedule.preferred_time = preferred_time
                    existing_schedule.timezone = timezone_str
                    existing_schedule.is_active = True
                    existing_schedule.save()
                    
                    # Schedule the first call
                    schedule_next_call(existing_schedule)
                    
                    messages.success(request, f'Call schedule reactivated successfully for {patient.user.email}')
                    return redirect('calling_agent:call_schedule_list')
            
            print(f"Debug: About to create schedule with:")
            print(f"  - Patient: {patient.user.email}")
            print(f"  - Frequency: {frequency}")
            print(f"  - Preferred day: {preferred_day}")
            print(f"  - Preferred time: {preferred_time}")
            print(f"  - Timezone: {timezone_str}")
            
            # Create new schedule
            schedule = CallSchedule.objects.create(
                patient=patient,
                frequency=frequency,
                preferred_day=preferred_day,
                preferred_time=preferred_time,
                timezone=timezone_str,
                is_active=True
            )
            
            print(f"Debug: Created schedule {schedule.id} for {patient.user.email}")
            
            # Schedule the first call
            call_created = schedule_next_call(schedule)
            print(f"Debug: Call creation result: {call_created}")
            
            # Verify the call was created
            call_sessions = CallSession.objects.filter(call_schedule=schedule)
            print(f"Debug: Call sessions for this schedule: {call_sessions.count()}")
            for session in call_sessions:
                print(f"Debug: Session {session.id} - Status: {session.status}, Time: {session.scheduled_time}")
            
            messages.success(request, f'Call schedule created successfully for {patient.user.email}')
            return redirect('calling_agent:call_schedule_list')
            
        except Exception as e:
            messages.error(request, f'Error creating call schedule: {str(e)}')
    
    # GET request - show form
    patients = Patient.objects.select_related('user').all()
    context = {
        'patients': patients,
        'title': 'Create Call Schedule',
        'day_choices': CallSchedule.DAY_CHOICES,
        'frequency_choices': CallSchedule.FREQUENCY_CHOICES,
    }
    return render(request, 'calling_agent/create_schedule.html', context)


@login_required
@user_passes_test(is_staff_or_admin)
def edit_call_schedule(request, schedule_id):
    """Edit an existing call schedule"""
    schedule = get_object_or_404(CallSchedule, id=schedule_id)
    
    if request.method == 'POST':
        try:
            schedule.frequency = request.POST.get('frequency', schedule.frequency)
            schedule.preferred_day = int(request.POST.get('preferred_day', schedule.preferred_day))
            schedule.preferred_time = request.POST.get('preferred_time', schedule.preferred_time)
            schedule.timezone = request.POST.get('timezone', schedule.timezone)
            schedule.is_active = request.POST.get('is_active') == 'on'
            schedule.save()
            
            messages.success(request, 'Call schedule updated successfully')
            return redirect('calling_agent:call_schedule_list')
            
        except Exception as e:
            messages.error(request, f'Error updating call schedule: {str(e)}')
    
    context = {
        'schedule': schedule,
        'title': f'Edit Call Schedule - {schedule.patient.user.email}',
        'day_choices': CallSchedule.DAY_CHOICES,
        'frequency_choices': CallSchedule.FREQUENCY_CHOICES,
    }
    return render(request, 'calling_agent/edit_schedule.html', context)


@login_required
@user_passes_test(is_staff_or_admin)
def delete_call_schedule(request, schedule_id):
    """Delete/deactivate a call schedule"""
    schedule = get_object_or_404(CallSchedule, id=schedule_id)
    
    if request.method == 'POST':
        # Cancel any scheduled calls for this schedule
        CallSession.objects.filter(
            call_schedule=schedule,
            status='scheduled'
        ).update(status='cancelled')
        
        # Actually delete the schedule instead of just deactivating
        patient_email = schedule.patient.user.email
        schedule.delete()
        
        messages.success(request, f'Call schedule deleted successfully for {patient_email}')
    
    return redirect('calling_agent:call_schedule_list')


@login_required
@user_passes_test(is_staff_or_admin)
def upcoming_calls(request):
    """View upcoming scheduled calls"""
    # Get current time
    now = timezone.now()
    
    # Debug: Let's also get all call sessions to see what's in the database
    all_calls = CallSession.objects.all().count()
    scheduled_calls = CallSession.objects.filter(status='scheduled').count()
    
    print(f"Debug: Total calls in DB: {all_calls}")
    print(f"Debug: Scheduled calls: {scheduled_calls}")
    print(f"Debug: Current time: {now}")
    
    # Get upcoming calls (including those scheduled for today/future)
    upcoming = CallSession.objects.filter(
        status='scheduled',
        scheduled_time__gte=now - timedelta(hours=1)  # Include calls from last hour in case of timezone issues
    ).select_related('patient__user', 'call_schedule').order_by('scheduled_time')[:20]
    
    print(f"Debug: Upcoming calls found: {upcoming.count()}")
    
    # Debug: Print details of upcoming calls
    for call in upcoming:
        print(f"Debug: Call for {call.patient.user.email} at {call.scheduled_time} (status: {call.status})")
    
    context = {
        'upcoming_calls': upcoming,
        'title': 'Upcoming Calls',
        'debug_info': {
            'total_calls': all_calls,
            'scheduled_calls': scheduled_calls,
            'current_time': now,
            'upcoming_count': upcoming.count()
        }
    }
    return render(request, 'calling_agent/upcoming_calls.html', context)


@csrf_exempt
def trigger_weekly_scheduling(request):
    """API endpoint to trigger weekly call scheduling (for cron jobs)"""
    if request.method == 'POST':
        try:
            # This would typically be called by a cron job or Celery task
            scheduled_count = schedule_all_weekly_calls()
            return JsonResponse({
                'status': 'success',
                'message': f'Scheduled {scheduled_count} calls'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'POST method required'}, status=400)


def schedule_next_call(call_schedule):
    """Helper function to schedule the next call for a given schedule"""
    try:
        print(f"=== Starting schedule_next_call ===")
        # Calculate next call date
        now = timezone.now()
        print(f"Debug schedule_next_call: Current time: {now}")
        print(f"Debug schedule_next_call: Call schedule for {call_schedule.patient.user.email}")
        print(f"Debug schedule_next_call: Preferred day: {call_schedule.preferred_day}")
        print(f"Debug schedule_next_call: Preferred time: {call_schedule.preferred_time}")
        print(f"Debug schedule_next_call: Timezone: {call_schedule.timezone}")
        
        # Get the next occurrence of the preferred day
        current_weekday = now.weekday()
        print(f"Debug schedule_next_call: Current weekday: {current_weekday}")
        
        days_ahead = call_schedule.preferred_day - current_weekday
        print(f"Debug schedule_next_call: Days ahead calculation: {call_schedule.preferred_day} - {current_weekday} = {days_ahead}")
        
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
            print(f"Debug schedule_next_call: Adjusted days ahead: {days_ahead}")
        
        next_call_date = now.date() + timedelta(days=days_ahead)
        print(f"Debug schedule_next_call: Next call date: {next_call_date}")
        
        # Combine with preferred time
        print(f"Debug schedule_next_call: Combining date {next_call_date} with time {call_schedule.preferred_time}")
        next_call_datetime = timezone.datetime.combine(
            next_call_date, 
            call_schedule.preferred_time
        )
        print(f"Debug schedule_next_call: Combined datetime (naive): {next_call_datetime}")
        
        # Make timezone-aware
        if timezone.is_naive(next_call_datetime):
            next_call_datetime = timezone.make_aware(next_call_datetime)
            print(f"Debug schedule_next_call: Made timezone-aware: {next_call_datetime}")
        
        print(f"Debug schedule_next_call: Final next call datetime: {next_call_datetime}")
        
        # Check if a call is already scheduled for this time
        existing_calls = CallSession.objects.filter(
            call_schedule=call_schedule,
            scheduled_time=next_call_datetime,
            status='scheduled'
        )
        existing_call_exists = existing_calls.exists()
        print(f"Debug schedule_next_call: Existing call exists: {existing_call_exists}")
        if existing_call_exists:
            print(f"Debug schedule_next_call: Existing calls: {list(existing_calls.values())}")
        
        if not existing_call_exists:
            print(f"Debug schedule_next_call: Creating new call session...")
            call_session = CallSession.objects.create(
                patient=call_schedule.patient,
                call_schedule=call_schedule,
                scheduled_time=next_call_datetime,
                status='scheduled'
            )
            print(f"Debug schedule_next_call: Created call session: {call_session.id}")
            print(f"Debug schedule_next_call: Call session details - Patient: {call_session.patient.user.email}, Time: {call_session.scheduled_time}, Status: {call_session.status}")
            
            # Verify it was saved
            saved_session = CallSession.objects.get(id=call_session.id)
            print(f"Debug schedule_next_call: Verified saved session: {saved_session.id}")
            
            return True
        else:
            print(f"Debug schedule_next_call: Call already exists, not creating new one")
            return False
        
    except Exception as e:
        print(f"ERROR in schedule_next_call: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def schedule_all_weekly_calls():
    """Schedule calls for all active weekly schedules"""
    active_schedules = CallSchedule.objects.filter(is_active=True, frequency='weekly')
    scheduled_count = 0
    
    for schedule in active_schedules:
        if schedule_next_call(schedule):
            scheduled_count += 1
    
    return scheduled_count


@login_required
@user_passes_test(is_staff_or_admin)
def initiate_call(request, call_session_id):
    """Manually initiate a call for a scheduled session"""
    call_session = get_object_or_404(CallSession, id=call_session_id)
    
    if call_session.status != 'scheduled':
        messages.error(request, f'Cannot initiate call. Current status: {call_session.get_status_display()}')
        return redirect('calling_agent:upcoming_calls')
    
    try:
        # Initialize Twilio service
        twilio_service = TwilioCallService()
        
        # Make the call
        success, call_sid, error = twilio_service.make_call(call_session)
        
        if success:
            # Update call session
            call_session.status = 'in_progress'
            call_session.call_sid = call_sid
            call_session.actual_start_time = timezone.now()
            call_session.save()
            
            messages.success(request, f'Call initiated successfully to {call_session.patient.user.email}')
        else:
            # Update call session as failed
            call_session.status = 'failed'
            call_session.notes = error
            call_session.save()
            
            messages.error(request, f'Failed to initiate call: {error}')
    
    except Exception as e:
        messages.error(request, f'Error initiating call: {str(e)}')
    
    return redirect('calling_agent:upcoming_calls')


@csrf_exempt
def twilio_webhook(request, call_session_id):
    """
    Twilio webhook to handle call conversation flow
    """
    call_session = get_object_or_404(CallSession, id=call_session_id)
    twilio_service = TwilioCallService()
    
    # Get current step from query params
    step = int(request.GET.get('step', 0))
    response_type = request.GET.get('response', None)
    
    # Process response if this is a callback with response data
    if response_type:
        if response_type == 'dtmf':
            digits = request.POST.get('Digits', '')
            twilio_service.process_response(call_session, step, digits, 'dtmf')
        elif response_type == 'speech':
            recording_url = request.POST.get('RecordingUrl', '')
            twilio_service.process_response(call_session, step, recording_url, 'speech')
        
        # Move to next step
        step += 1
    
    # Generate TwiML for current step
    twiml = twilio_service.create_conversation_twiml(call_session, step)
    
    return HttpResponse(twiml, content_type='text/xml')


@csrf_exempt
def twilio_status_callback(request, call_session_id):
    """
    Twilio status callback to track call status changes
    """
    call_session = get_object_or_404(CallSession, id=call_session_id)
    
    # Get status from Twilio
    call_status = request.POST.get('CallStatus', '')
    call_duration = request.POST.get('CallDuration', '')
    recording_url = request.POST.get('RecordingUrl', '')
    
    # Update call session based on status
    if call_status == 'ringing':
        call_session.status = 'in_progress'
    elif call_status == 'answered':
        call_session.status = 'in_progress'
        if not call_session.actual_start_time:
            call_session.actual_start_time = timezone.now()
    elif call_status in ['completed', 'busy', 'no-answer', 'failed', 'canceled']:
        if call_status == 'completed':
            call_session.status = 'completed'
        elif call_status == 'busy':
            call_session.status = 'busy'
        elif call_status == 'no-answer':
            call_session.status = 'no_answer'
        else:
            call_session.status = 'failed'
        
        # Set end time and duration
        call_session.actual_end_time = timezone.now()
        if call_duration:
            try:
                call_session.call_duration = timedelta(seconds=int(call_duration))
            except:
                pass
        
        # Save recording URL if available
        if recording_url:
            call_session.recording_url = recording_url
        
        # Schedule next call if this was successful
        if call_status == 'completed':
            schedule_next_call(call_session.call_schedule)
    
    call_session.save()
    
    return HttpResponse(status=200)


@login_required
@user_passes_test(is_staff_or_admin)
def call_history(request):
    """View call history"""
    calls = CallSession.objects.select_related('patient__user', 'call_schedule').order_by('-scheduled_time')[:50]
    
    context = {
        'calls': calls,
        'title': 'Call History'
    }
    return render(request, 'calling_agent/call_history.html', context)


@login_required
@user_passes_test(is_staff_or_admin)
def call_details(request, call_session_id):
    """View detailed information about a specific call"""
    call_session = get_object_or_404(CallSession, id=call_session_id)
    responses = call_session.responses.select_related('question').order_by('question__order')
    alerts = call_session.alerts.order_by('-created_at')
    
    context = {
        'call_session': call_session,
        'responses': responses,
        'alerts': alerts,
        'title': f'Call Details - {call_session.patient.user.email}'
    }
    return render(request, 'calling_agent/call_details.html', context)


@login_required
@user_passes_test(is_staff_or_admin)
def debug_calls(request):
    """Debug view to see all call sessions"""
    all_calls = CallSession.objects.select_related('patient__user', 'call_schedule').order_by('-created_at')
    
    context = {
        'all_calls': all_calls,
        'title': 'All Call Sessions (Debug)',
        'current_time': timezone.now()
    }
    return render(request, 'calling_agent/debug_calls.html', context)


@login_required
@user_passes_test(is_staff_or_admin)
def test_call_creation(request):
    """Test view to manually create a call session"""
    if request.method == 'POST':
        try:
            # Get the first active schedule
            schedule = CallSchedule.objects.filter(is_active=True).first()
            if not schedule:
                messages.error(request, 'No active schedule found to test with')
                return redirect('calling_agent:call_schedule_list')
            
            # Create a test call session
            test_time = timezone.now() + timedelta(hours=1)
            call_session = CallSession.objects.create(
                patient=schedule.patient,
                call_schedule=schedule,
                scheduled_time=test_time,
                status='scheduled'
            )
            
            messages.success(request, f'Test call session created: {call_session.id}')
            
            # Verify it exists
            total_calls = CallSession.objects.count()
            messages.info(request, f'Total call sessions in DB: {total_calls}')
            
        except Exception as e:
            messages.error(request, f'Error creating test call: {str(e)}')
            import traceback
            traceback.print_exc()
    
    return redirect('calling_agent:call_schedule_list')
