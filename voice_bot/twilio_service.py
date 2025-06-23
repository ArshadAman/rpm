from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import os
import logging
from ..fsdaf.models import VoiceInteraction
from .services import VoiceBotManager

logger = logging.getLogger(__name__)

class TwilioVoiceService:
    """
    Service for handling Twilio voice calls
    """
    
    def __init__(self):
        self.account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', os.getenv('TWILIO_ACCOUNT_SID'))
        self.auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', os.getenv('TWILIO_AUTH_TOKEN'))
        self.phone_number = getattr(settings, 'TWILIO_PHONE_NUMBER', os.getenv('TWILIO_PHONE_NUMBER'))
        
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
        else:
            logger.error("Twilio credentials not configured")
            self.client = None
    
    def initiate_call(self, interaction: VoiceInteraction) -> bool:
        """
        Initiate an outbound call to the patient
        """
        if not self.client:
            logger.error("Twilio client not initialized")
            return False
        
        try:
            call = self.client.calls.create(
                to=interaction.phone_number,
                from_=self.phone_number,
                url=f"{settings.BASE_URL}/voice-bot/handle-call/{interaction.id}/",
                method='POST',
                record=True,
                status_callback=f"{settings.BASE_URL}/voice-bot/call-status/{interaction.id}/"
            )
            
            interaction.twilio_call_sid = call.sid
            interaction.call_status = 'in_progress'
            interaction.save()
            
            logger.info(f"Call initiated for interaction {interaction.id}, Twilio SID: {call.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Error initiating call: {str(e)}")
            interaction.call_status = 'failed'
            interaction.save()
            return False
    
    def generate_twiml_response(self, message: str, gather_input: bool = True) -> str:
        """
        Generate TwiML response for voice interactions
        """
        response = VoiceResponse()
        
        if gather_input:
            gather = Gather(
                input='speech',
                timeout=10,
                speech_timeout='auto',
                action='/voice-bot/process-speech/',
                method='POST'
            )
            gather.say(message, voice='alice')
            response.append(gather)
            
            # Fallback if no input received
            response.say("I didn't hear anything. Please try speaking again or press any key to end the call.")
            response.redirect('/voice-bot/handle-call/')
        else:
            response.say(message, voice='alice')
            response.hangup()
        
        return str(response)

# Webhook views for Twilio
@csrf_exempt
@require_POST
def handle_call(request, interaction_id):
    """
    Handle incoming Twilio call webhook
    """
    try:
        interaction = VoiceInteraction.objects.get(id=interaction_id)
        bot_manager = VoiceBotManager()
        
        # Get the first question to ask
        next_question = bot_manager.question_engine.get_next_question(interaction)
        
        if next_question:
            message = f"Hello {interaction.patient.user.first_name}. This is your RPM health assistant. {next_question.question_text}"
        else:
            message = f"Hello {interaction.patient.user.first_name}. This is your RPM health assistant. How are you feeling today?"
        
        twilio_service = TwilioVoiceService()
        twiml = twilio_service.generate_twiml_response(message, gather_input=True)
        
        return HttpResponse(twiml, content_type='text/xml')
        
    except VoiceInteraction.DoesNotExist:
        logger.error(f"Voice interaction {interaction_id} not found")
        response = VoiceResponse()
        response.say("Sorry, there was an error with your call.")
        response.hangup()
        return HttpResponse(str(response), content_type='text/xml')

@csrf_exempt
@require_POST
def process_speech(request):
    """
    Process patient's speech input
    """
    try:
        # Get speech result from Twilio
        speech_result = request.POST.get('SpeechResult', '')
        call_sid = request.POST.get('CallSid', '')
        
        # Find the interaction by call SID
        interaction = VoiceInteraction.objects.get(twilio_call_sid=call_sid)
        
        if speech_result:
            bot_manager = VoiceBotManager()
            
            # Process the patient's response
            result = bot_manager.process_patient_response(
                interaction, 
                speech_result
            )
            
            # Generate response
            ai_response = result['ai_response']
            next_question = result.get('next_question')
            
            if next_question:
                message = f"{ai_response} Now, {next_question.question_text}"
                gather_input = True
            else:
                message = f"{ai_response} Thank you for completing your health check. Have a great day!"
                gather_input = False
                # End the interaction
                bot_manager.end_interaction(interaction)
            
            twilio_service = TwilioVoiceService()
            twiml = twilio_service.generate_twiml_response(message, gather_input)
            
            return HttpResponse(twiml, content_type='text/xml')
        else:
            # No speech detected
            response = VoiceResponse()
            response.say("I didn't catch that. Could you please repeat?")
            response.redirect('/voice-bot/handle-call/')
            return HttpResponse(str(response), content_type='text/xml')
            
    except VoiceInteraction.DoesNotExist:
        logger.error(f"Voice interaction not found for call SID {call_sid}")
        response = VoiceResponse()
        response.say("Sorry, there was an error processing your response.")
        response.hangup()
        return HttpResponse(str(response), content_type='text/xml')
    except Exception as e:
        logger.error(f"Error processing speech: {str(e)}")
        response = VoiceResponse()
        response.say("Sorry, there was an error. Please try again later.")
        response.hangup()
        return HttpResponse(str(response), content_type='text/xml')

@csrf_exempt
@require_POST
def call_status_callback(request, interaction_id):
    """
    Handle call status updates from Twilio
    """
    try:
        call_status = request.POST.get('CallStatus', '')
        call_duration = request.POST.get('CallDuration', '')
        
        interaction = VoiceInteraction.objects.get(id=interaction_id)
        
        # Update interaction status
        if call_status == 'completed':
            interaction.call_status = 'completed'
            if call_duration:
                from datetime import timedelta
                interaction.call_duration = timedelta(seconds=int(call_duration))
        elif call_status == 'failed':
            interaction.call_status = 'failed'
        elif call_status == 'no-answer':
            interaction.call_status = 'no_answer'
        
        interaction.save()
        
        return HttpResponse('OK')
        
    except VoiceInteraction.DoesNotExist:
        logger.error(f"Voice interaction {interaction_id} not found")
        return HttpResponse('Error', status=404)
    except Exception as e:
        logger.error(f"Error handling call status: {str(e)}")
        return HttpResponse('Error', status=500)
