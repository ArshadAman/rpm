import os
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)
print(getattr(settings, 'BASE_URL', 'BASE_URL not set'))

class TwilioCallService:
    """Service class to handle Twilio voice calls"""
    
    def __init__(self):
        # Get Twilio credentials from environment or settings
        self.account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', os.environ.get('TWILIO_ACCOUNT_SID'))
        self.auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', os.environ.get('TWILIO_AUTH_TOKEN'))
        self.phone_number = getattr(settings, 'TWILIO_PHONE_NUMBER', os.environ.get('TWILIO_PHONE_NUMBER'))
        
        if not all([self.account_sid, self.auth_token, self.phone_number]):
            raise ValueError("Twilio credentials not properly configured")
        
        self.client = Client(self.account_sid, self.auth_token)
    
    def make_call(self, call_session):
        """
        Initiate a call to the patient
        
        Args:
            call_session: CallSession instance
            
        Returns:
            tuple: (success: bool, call_sid: str or None, error: str or None)
        """
        try:
            patient = call_session.patient
            
            # Check if patient has a phone number
            if not patient.phone_number:
                logger.error(f"No phone number for patient {patient.user.email}")
                return False, None, "Patient has no phone number"
            
            # Format phone number (ensure it has country code)
            to_number = self.format_phone_number(patient.phone_number)
            
            # Create the webhook URL for handling the call
            webhook_url = self.get_webhook_url(call_session.id)
            
            # Make the call
            call = self.client.calls.create(
                to=to_number,
                from_=self.phone_number,
                url=webhook_url,
                method='POST',
                record=True,  # Record the call
                timeout=30,   # Ring for 30 seconds
                status_callback=self.get_status_callback_url(call_session.id),
                status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
                status_callback_method='POST'
            )
            
            logger.info(f"Call initiated: {call.sid} to {to_number}")
            return True, call.sid, None
            
        except Exception as e:
            error_msg = f"Error making call: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def format_phone_number(self, phone_number):
        """Format phone number for Twilio (ensure E.164 format)"""
        # Remove all non-digit characters
        digits_only = ''.join(filter(str.isdigit, phone_number))
        
        # If it doesn't start with country code, assume US (+1)
        if len(digits_only) == 10:
            return f"+1{digits_only}"
        elif len(digits_only) == 11 and digits_only.startswith('1'):
            return f"+{digits_only}"
        elif not digits_only.startswith('+'):
            return f"+{digits_only}"
        else:
            return digits_only
    
    def get_webhook_url(self, call_session_id):
        """Get the webhook URL for handling the call conversation"""
        # This would be your domain + the webhook endpoint
        base_url = getattr(settings, 'BASE_URL', 'https://yourdomain.com')
        print('base', base_url)
        print('base', base_url)
        return f"{base_url}/calling-agent/api/webhook/{call_session_id}/"
    
    def get_status_callback_url(self, call_session_id):
        """Get the status callback URL for call status updates"""
        base_url = getattr(settings, 'BASE_URL', 'https://yourdomain.com')
        return f"{base_url}/calling-agent/api/status/{call_session_id}/"
    
    def create_conversation_twiml(self, call_session, step=0):
        """
        Create TwiML for the conversation flow
        
        Args:
            call_session: CallSession instance
            step: Current step in the conversation
            
        Returns:
            str: TwiML response
        """
        response = VoiceResponse()
        
        if step == 0:
            # Welcome message
            patient_name = call_session.patient.user.first_name or "there"
            welcome_message = f"Hello {patient_name}, this is your weekly health check call from your healthcare team. I'll be asking you a few quick questions about how you're feeling. Let's get started."
            
            response.say(welcome_message, voice='alice', language='en-US')
            response.pause(length=1)
            
            # Redirect to first question
            response.redirect(
                url=self.get_webhook_url(call_session.id) + f"?step=1",
                method='POST'
            )
        
        else:
            # Handle questions based on step
            questions = self.get_questions_for_call()
            
            if step <= len(questions):
                question = questions[step - 1]
                
                # Ask the question
                response.say(question['text'], voice='alice', language='en-US')
                
                if question['type'] == 'scale':
                    response.say("Please press a number from 1 to 10 on your keypad.", voice='alice')
                    response.gather(
                        input='dtmf',
                        timeout=10,
                        num_digits=1,
                        action=self.get_webhook_url(call_session.id) + f"?step={step}&response=dtmf",
                        method='POST'
                    )
                elif question['type'] == 'yes_no':
                    response.say("Press 1 for yes, or 2 for no.", voice='alice')
                    response.gather(
                        input='dtmf',
                        timeout=10,
                        num_digits=1,
                        action=self.get_webhook_url(call_session.id) + f"?step={step}&response=dtmf",
                        method='POST'
                    )
                else:
                    # Open ended - record response
                    response.say("Please speak your answer after the beep. Press any key when finished.", voice='alice')
                    response.record(
                        timeout=30,
                        max_length=120,
                        action=self.get_webhook_url(call_session.id) + f"?step={step}&response=speech",
                        method='POST'
                    )
            else:
                # End of questions
                response.say("Thank you for completing your health check. Your responses have been recorded. Have a great day!", voice='alice')
                response.hangup()
        
        return str(response)
    
    def get_questions_for_call(self):
        """Get predefined questions for the call"""
        # This could be made dynamic by fetching from CallQuestionTemplate
        return [
            {
                'text': 'On a scale of 1 to 10, how would you rate your overall health today?',
                'type': 'scale',
                'key': 'overall_health'
            },
            {
                'text': 'Have you taken your medications as prescribed today?',
                'type': 'yes_no',
                'key': 'medication_taken'
            },
            {
                'text': 'On a scale of 1 to 10, how would you rate your pain level today?',
                'type': 'scale',
                'key': 'pain_level'
            },
            {
                'text': 'Are you experiencing any unusual symptoms or concerns?',
                'type': 'yes_no',
                'key': 'unusual_symptoms'
            },
            {
                'text': 'How many hours did you sleep last night?',
                'type': 'open_ended',
                'key': 'sleep_hours'
            }
        ]
    
    def process_response(self, call_session, step, response_data, response_type):
        """
        Process and save patient response
        
        Args:
            call_session: CallSession instance
            step: Question step number
            response_data: The response data (digits or recording URL)
            response_type: 'dtmf' or 'speech'
        """
        from .models import CallResponse, CallQuestionTemplate
        
        questions = self.get_questions_for_call()
        if step <= len(questions):
            question_data = questions[step - 1]
            
            # Create or get question template (you might want to pre-create these)
            question_template, created = CallQuestionTemplate.objects.get_or_create(
                question_text=question_data['text'],
                defaults={
                    'question_type': question_data['type'],
                    'order': step,
                    'is_active': True
                }
            )
            
            # Save the response
            call_response = CallResponse.objects.create(
                call_session=call_session,
                question=question_template,
                response_text=str(response_data),
                processed_response=self.process_raw_response(response_data, question_data['type']),
                numeric_value=self.extract_numeric_value(response_data, question_data['type']),
                confidence_score=1.0 if response_type == 'dtmf' else 0.8
            )
            
            # Check if response is concerning
            if self.is_concerning_response(call_response, question_data):
                call_response.is_concerning = True
                call_response.save()
                self.create_alert_for_response(call_response)
    
    def process_raw_response(self, response_data, question_type):
        """Process raw response based on question type"""
        if question_type == 'scale':
            return f"Rating: {response_data}/10"
        elif question_type == 'yes_no':
            return "Yes" if response_data == '1' else "No"
        else:
            return str(response_data)
    
    def extract_numeric_value(self, response_data, question_type):
        """Extract numeric value from response if applicable"""
        if question_type == 'scale':
            try:
                return float(response_data)
            except:
                return None
        return None
    
    def is_concerning_response(self, call_response, question_data):
        """Check if a response should be flagged as concerning"""
        if question_data['key'] == 'overall_health' and call_response.numeric_value and call_response.numeric_value <= 3:
            return True
        elif question_data['key'] == 'pain_level' and call_response.numeric_value and call_response.numeric_value >= 8:
            return True
        elif question_data['key'] == 'unusual_symptoms' and call_response.response_text == '1':
            return True
        return False
    
    def create_alert_for_response(self, call_response):
        """Create an alert for concerning responses"""
        from .models import CallAlert
        
        CallAlert.objects.create(
            call_session=call_response.call_session,
            call_response=call_response,
            patient=call_response.call_session.patient,
            alert_type='critical_response',
            severity='high',
            title=f"Concerning Response: {call_response.question.question_text[:50]}",
            description=f"Patient responded: {call_response.processed_response}"
        )
