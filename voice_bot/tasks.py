from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging
from ..fsdaf.models import VoiceInteraction, VoiceCallSchedule
from .services import VoiceBotManager
from .twilio_service import TwilioVoiceService
from rpm_users.models import Patient

logger = logging.getLogger(__name__)

@shared_task
def schedule_voice_calls():
    """
    Periodic task to schedule voice calls for patients
    """
    logger.info("Running scheduled voice calls task")
    
    # Get all active call schedules that need calls
    now = timezone.now()
    schedules = VoiceCallSchedule.objects.filter(
        is_active=True,
        next_call_scheduled__lte=now
    )
    
    for schedule in schedules:
        try:
            # Create voice interaction
            bot_manager = VoiceBotManager()
            interaction = bot_manager.start_voice_interaction(
                schedule.patient, 
                'outbound_scheduled'
            )
            
            # Schedule the actual call
            initiate_voice_call.delay(interaction.id)
            
            # Update next call time
            schedule.next_call_scheduled = calculate_next_call_time(schedule)
            schedule.save()
            
            logger.info(f"Scheduled call for patient {schedule.patient.user.get_full_name()}")
            
        except Exception as e:
            logger.error(f"Error scheduling call for patient {schedule.patient.id}: {str(e)}")

@shared_task
def initiate_voice_call(interaction_id):
    """
    Task to initiate a voice call
    """
    try:
        interaction = VoiceInteraction.objects.get(id=interaction_id)
        
        twilio_service = TwilioVoiceService()
        success = twilio_service.initiate_call(interaction)
        
        if success:
            logger.info(f"Successfully initiated call for interaction {interaction_id}")
        else:
            logger.error(f"Failed to initiate call for interaction {interaction_id}")
            
    except VoiceInteraction.DoesNotExist:
        logger.error(f"Voice interaction {interaction_id} not found")
    except Exception as e:
        logger.error(f"Error initiating call: {str(e)}")

@shared_task
def process_emergency_call(patient_id, urgency_level):
    """
    Task to handle emergency calls
    """
    try:
        patient = Patient.objects.get(id=patient_id)
        
        # Create emergency interaction
        bot_manager = VoiceBotManager()
        interaction = bot_manager.start_voice_interaction(
            patient, 
            'emergency_check'
        )
        
        # Initiate immediate call
        twilio_service = TwilioVoiceService()
        twilio_service.initiate_call(interaction)
        
        # Send alerts to healthcare providers
        send_emergency_alert.delay(patient_id, urgency_level, interaction.id)
        
        logger.info(f"Emergency call initiated for patient {patient.user.get_full_name()}")
        
    except Patient.DoesNotExist:
        logger.error(f"Patient {patient_id} not found for emergency call")
    except Exception as e:
        logger.error(f"Error processing emergency call: {str(e)}")

@shared_task
def send_emergency_alert(patient_id, urgency_level, interaction_id):
    """
    Send emergency alerts to healthcare providers
    """
    try:
        patient = Patient.objects.get(id=patient_id)
        interaction = VoiceInteraction.objects.get(id=interaction_id)
        
        # Get the moderator/healthcare provider
        if patient.moderator_assigned:
            # Send email or SMS alert
            from django.core.mail import send_mail
            from django.conf import settings
            
            subject = f"URGENT: Voice Bot Emergency Alert - {patient.user.get_full_name()}"
            message = f"""
            Emergency alert from voice bot interaction:
            
            Patient: {patient.user.get_full_name()}
            Urgency Level: {urgency_level}
            Interaction ID: {interaction_id}
            Time: {interaction.created_at}
            
            Health Alerts: {interaction.health_alerts}
            
            Please contact the patient immediately.
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [patient.moderator_assigned.user.email],
                fail_silently=False,
            )
            
            logger.info(f"Emergency alert sent for patient {patient.user.get_full_name()}")
        
    except (Patient.DoesNotExist, VoiceInteraction.DoesNotExist):
        logger.error(f"Patient or interaction not found for emergency alert")
    except Exception as e:
        logger.error(f"Error sending emergency alert: {str(e)}")

@shared_task
def analyze_voice_interactions():
    """
    Periodic task to analyze voice interactions for patterns and insights
    """
    logger.info("Running voice interaction analysis")
    
    # Get recent interactions
    week_ago = timezone.now() - timedelta(days=7)
    interactions = VoiceInteraction.objects.filter(
        created_at__gte=week_ago,
        call_status='completed'
    )
    
    # Analyze patterns (this could be expanded with ML)
    for interaction in interactions:
        try:
            # Check for concerning patterns
            responses = interaction.patient_responses or []
            
            # Simple keyword analysis
            concerning_keywords = ['pain', 'chest pain', 'dizzy', 'shortness of breath', 'emergency']
            for response in responses:
                for keyword in concerning_keywords:
                    if keyword.lower() in response.lower():
                        # Flag for follow-up
                        interaction.follow_up_required = True
                        interaction.save()
                        break
                        
        except Exception as e:
            logger.error(f"Error analyzing interaction {interaction.id}: {str(e)}")

def calculate_next_call_time(schedule: VoiceCallSchedule):
    """
    Calculate the next call time based on schedule frequency
    """
    now = timezone.now()
    
    if schedule.frequency == 'daily':
        return now + timedelta(days=1)
    elif schedule.frequency == 'weekly':
        return now + timedelta(weeks=1)
    elif schedule.frequency == 'bi_weekly':
        return now + timedelta(weeks=2)
    elif schedule.frequency == 'monthly':
        return now + timedelta(days=30)
    else:
        # Default to weekly
        return now + timedelta(weeks=1)
