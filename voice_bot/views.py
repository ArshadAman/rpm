from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import json
from .models import VoiceInteraction, VoiceCallSchedule, VoiceQuestion
from .services import VoiceBotManager
from .tasks import initiate_voice_call, process_emergency_call
from rpm_users.models import Patient, Moderator

@login_required
def voice_bot_dashboard(request):
    """
    Dashboard for voice bot management
    """
    # Check if user is a moderator
    try:
        moderator = Moderator.objects.get(user=request.user)
    except Moderator.DoesNotExist:
        messages.error(request, "Access denied. Only moderators can access voice bot features.")
        return redirect('home')
    
    # Get patients assigned to this moderator
    patients = Patient.objects.filter(moderator_assigned=moderator)
    
    # Get recent voice interactions
    recent_interactions = VoiceInteraction.objects.filter(
        patient__in=patients
    ).order_by('-created_at')[:10]
    
    # Get scheduled calls
    scheduled_calls = VoiceCallSchedule.objects.filter(
        patient__in=patients,
        is_active=True
    )
    
    # Get interactions requiring follow-up
    follow_up_required = VoiceInteraction.objects.filter(
        patient__in=patients,
        follow_up_required=True,
        call_status='completed'
    )
    
    context = {
        'patients': patients,
        'recent_interactions': recent_interactions,
        'scheduled_calls': scheduled_calls,
        'follow_up_required': follow_up_required,
        'total_patients': patients.count(),
        'active_schedules': scheduled_calls.count(),
        'pending_follow_ups': follow_up_required.count(),
    }
    
    return render(request, 'voice_bot/dashboard.html', context)

@login_required
def schedule_voice_calls(request, patient_id):
    """
    Schedule voice calls for a patient
    """
    patient = get_object_or_404(Patient, id=patient_id)
    
    # Check if user has permission
    if not request.user.is_superuser:
        try:
            moderator = Moderator.objects.get(user=request.user)
            if patient.moderator_assigned != moderator:
                messages.error(request, "You don't have permission to schedule calls for this patient.")
                return redirect('voice_bot_dashboard')
        except Moderator.DoesNotExist:
            messages.error(request, "Access denied.")
            return redirect('home')
    
    if request.method == 'POST':
        frequency = request.POST.get('frequency', 'weekly')
        preferred_time = request.POST.get('preferred_time', '10:00')
        timezone_str = request.POST.get('timezone', 'UTC')
        
        # Create or update call schedule
        schedule, created = VoiceCallSchedule.objects.get_or_create(
            patient=patient,
            defaults={
                'frequency': frequency,
                'preferred_time': preferred_time,
                'timezone': timezone_str,
                'is_active': True,
                'next_call_scheduled': timezone.now() + timezone.timedelta(days=1)
            }
        )
        
        if not created:
            schedule.frequency = frequency
            schedule.preferred_time = preferred_time
            schedule.timezone = timezone_str
            schedule.is_active = True
            schedule.save()
        
        messages.success(request, f"Call schedule updated for {patient.user.get_full_name()}")
        return redirect('voice_bot_dashboard')
    
    # Get existing schedule
    try:
        schedule = VoiceCallSchedule.objects.get(patient=patient)
    except VoiceCallSchedule.DoesNotExist:
        schedule = None
    
    context = {
        'patient': patient,
        'schedule': schedule,
        'frequency_choices': VoiceCallSchedule.FREQUENCY_CHOICES,
    }
    
    return render(request, 'voice_bot/schedule_calls.html', context)

@login_required
def patient_voice_interactions(request, patient_id):
    """
    View voice interactions for a specific patient
    """
    patient = get_object_or_404(Patient, id=patient_id)
    
    # Check permissions
    if not request.user.is_superuser:
        try:
            moderator = Moderator.objects.get(user=request.user)
            if patient.moderator_assigned != moderator:
                messages.error(request, "You don't have permission to view this patient's data.")
                return redirect('voice_bot_dashboard')
        except Moderator.DoesNotExist:
            messages.error(request, "Access denied.")
            return redirect('home')
    
    interactions = VoiceInteraction.objects.filter(
        patient=patient
    ).order_by('-created_at')
    
    context = {
        'patient': patient,
        'interactions': interactions,
    }
    
    return render(request, 'voice_bot/patient_interactions.html', context)

@login_required
def voice_interaction_detail(request, interaction_id):
    """
    Detailed view of a voice interaction
    """
    interaction = get_object_or_404(VoiceInteraction, id=interaction_id)
    
    # Check permissions
    if not request.user.is_superuser:
        try:
            moderator = Moderator.objects.get(user=request.user)
            if interaction.patient.moderator_assigned != moderator:
                messages.error(request, "You don't have permission to view this interaction.")
                return redirect('voice_bot_dashboard')
        except Moderator.DoesNotExist:
            messages.error(request, "Access denied.")
            return redirect('home')
    
    # Prepare conversation data
    questions = interaction.questions_asked or []
    responses = interaction.patient_responses or []
    ai_responses = interaction.ai_responses or []
    
    conversation = []
    for i in range(max(len(questions), len(responses), len(ai_responses))):
        entry = {}
        if i < len(questions):
            entry['question'] = questions[i]
        if i < len(responses):
            entry['patient_response'] = responses[i]
        if i < len(ai_responses):
            entry['ai_response'] = ai_responses[i]
        conversation.append(entry)
    
    context = {
        'interaction': interaction,
        'conversation': conversation,
    }
    
    return render(request, 'voice_bot/interaction_detail.html', context)

@login_required
def initiate_manual_call(request, patient_id):
    """
    Manually initiate a voice call for a patient
    """
    patient = get_object_or_404(Patient, id=patient_id)
    
    # Check permissions
    if not request.user.is_superuser:
        try:
            moderator = Moderator.objects.get(user=request.user)
            if patient.moderator_assigned != moderator:
                messages.error(request, "You don't have permission to call this patient.")
                return redirect('voice_bot_dashboard')
        except Moderator.DoesNotExist:
            messages.error(request, "Access denied.")
            return redirect('home')
    
    if request.method == 'POST':
        try:
            # Create voice interaction
            bot_manager = VoiceBotManager()
            interaction = bot_manager.start_voice_interaction(
                patient, 
                'outbound_scheduled'
            )
            
            # Initiate call asynchronously
            initiate_voice_call.delay(interaction.id)
            
            messages.success(request, f"Call initiated for {patient.user.get_full_name()}")
            return JsonResponse({'success': True, 'interaction_id': interaction.id})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def patient_voice_summary(request, patient_id):
    """
    API endpoint for patient voice interaction summary
    """
    patient = get_object_or_404(Patient, id=patient_id)
    
    # Check permissions
    if not request.user.is_superuser:
        try:
            moderator = Moderator.objects.get(user=request.user)
            if patient.moderator_assigned != moderator:
                return JsonResponse({'error': 'Permission denied'}, status=403)
        except Moderator.DoesNotExist:
            return JsonResponse({'error': 'Access denied'}, status=403)
    
    interactions = VoiceInteraction.objects.filter(patient=patient).order_by('-created_at')
    
    summary = {
        'total_interactions': interactions.count(),
        'completed_calls': interactions.filter(call_status='completed').count(),
        'failed_calls': interactions.filter(call_status='failed').count(),
        'follow_ups_required': interactions.filter(follow_up_required=True).count(),
        'recent_interactions': []
    }
    
    # Add recent interactions
    for interaction in interactions[:5]:
        summary['recent_interactions'].append({
            'id': interaction.id,
            'type': interaction.get_interaction_type_display(),
            'status': interaction.get_call_status_display(),
            'created_at': interaction.created_at.isoformat(),
            'follow_up_required': interaction.follow_up_required,
            'health_alerts': len(interaction.health_alerts) if interaction.health_alerts else 0,
        })
    
    return JsonResponse(summary)

@csrf_exempt
def create_emergency_alert(request):
    """
    API endpoint to create emergency alerts
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            patient_id = data.get('patient_id')
            urgency_level = data.get('urgency_level', 'high')
            
            if not patient_id:
                return JsonResponse({'error': 'Patient ID required'}, status=400)
            
            # Trigger emergency call
            process_emergency_call.delay(patient_id, urgency_level)
            
            return JsonResponse({'success': True, 'message': 'Emergency call initiated'})
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)
