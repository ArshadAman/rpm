"""
Services for Retell AI integration and call management.
"""

import json
import logging
import re
import requests
from typing import Dict, Optional, Any, List
from django.conf import settings
from django.core.exceptions import ValidationError
from rpm_users.models import Patient
from .models import RetellCallSession
import google.generativeai as genai

try:
    import google.generativeai as genai
except ImportError:
    genai = None

logger = logging.getLogger('retell_calling.services')


class RetellCallService:
    """Service for managing Retell AI API interactions"""
    
    def __init__(self):
        """Initialize the Retell service with API configuration"""
        self.api_key = getattr(settings, 'RETELL_BEARER_TOKEN', None)
        self.base_url = "https://api.retellai.com/v2"
        self.from_number = getattr(settings, 'RETELL_FROM_NUMBER', None)
        
        if not self.api_key:
            logger.error("RETELL_BEARER_TOKEN not configured in settings")
            raise ValueError("Retell API key not configured")
        
        if not self.from_number:
            logger.error("RETELL_FROM_NUMBER not configured in settings")
            raise ValueError("Retell from number not configured")
        
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        logger.info("RetellCallService initialized successfully")
    
    def validate_phone_number(self, phone_number: str) -> str:
        """
        Validate and format phone number for Retell API.
        
        Args:
            phone_number: Raw phone number string
            
        Returns:
            Formatted phone number in E.164 format
            
        Raises:
            ValidationError: If phone number is invalid
        """
        if not phone_number:
            raise ValidationError("Phone number is required")
        
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone_number)
        
        # Check if it's empty after cleaning
        if not digits_only:
            raise ValidationError("Phone number contains no digits")
        
        # Handle US numbers (10 digits) - add country code
        if len(digits_only) == 10:
            formatted_number = f"+1{digits_only}"
        # Handle numbers with country code (11+ digits)
        elif len(digits_only) >= 11:
            # If it starts with 1 and has 11 digits, it's likely US with country code
            if digits_only.startswith('1') and len(digits_only) == 11:
                formatted_number = f"+{digits_only}"
            else:
                # For other international numbers, assume they already include country code
                formatted_number = f"+{digits_only}"
        else:
            raise ValidationError(f"Invalid phone number length: {len(digits_only)} digits")
        
        # Basic validation - ensure it looks like a valid phone number
        if len(formatted_number) < 10 or len(formatted_number) > 16:
            raise ValidationError(f"Phone number length invalid: {formatted_number}")
        
        logger.debug(f"Phone number validated and formatted: {phone_number} -> {formatted_number}")
        return formatted_number
    
    def create_phone_call(self, patient: Patient, agent_id: str = None, dynamic_variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a phone call using Retell API.
        
        Args:
            patient: Patient instance to call
            agent_id: Optional Retell agent ID (uses default if not provided)
            
        Returns:
            Dictionary containing call details and RetellCallSession instance
            
        Raises:
            ValidationError: If patient data is invalid
            requests.RequestException: If API call fails
        """
        logger.info(f"Initiating call for patient: {patient.user.email}")
        
        # Validate patient has phone number
        if not patient.phone_number:
            error_msg = f"Patient {patient.user.email} has no phone number"
            logger.error(error_msg)
            raise ValidationError(error_msg)
        
        # Validate and format phone numbers
        try:
            to_number = self.validate_phone_number(patient.phone_number)
            from_number = self.validate_phone_number(self.from_number)
        except ValidationError as e:
            logger.error(f"Phone number validation failed for patient {patient.user.email}: {e}")
            raise
        
        # Prepare API request payload
        payload = {
            "call_type": "phone_call",
            "from_number": from_number,
            "to_number": to_number,
        }
        
        # Add agent ID if provided
        if agent_id:
            payload["agent_id"] = agent_id
        
        # Add provided dynamic variables, merging with basic patient name if available
        if dynamic_variables is not None:
            payload["retell_llm_dynamic_variables"] = dynamic_variables
        elif patient.user.first_name:
            payload["retell_llm_dynamic_variables"] = {
                "patient_name": patient.user.first_name
            }
        
        logger.debug(f"Retell API payload: {payload}")
        
        try:
            # Make API request to Retell
            print("from",from_number,to_number)
            response = requests.post(
                f"{self.base_url}/create-phone-call",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            logger.info(f"Retell API response status: {response.status_code}")
            
            # Check if request was successful
            response.raise_for_status()
            
            # Parse response
            response_data = response.json()
            call_id = response_data.get('call_id')
            
            if not call_id:
                error_msg = "No call_id returned from Retell API"
                logger.error(f"{error_msg}. Response: {response_data}")
                raise ValueError(error_msg)
            
            logger.info(f"Call created successfully with ID: {call_id}")
            
            # Create RetellCallSession record
            call_session = RetellCallSession.objects.create(
                patient=patient,
                retell_call_id=call_id,
                call_status='initiated',
                from_number=from_number,
                to_number=to_number,
                agent_id=agent_id or ''
            )
            
            logger.info(f"RetellCallSession created with ID: {call_session.id}")
            
            return {
                'success': True,
                'call_id': call_id,
                'call_session': call_session,
                'response_data': response_data
            }
            
        except requests.exceptions.Timeout:
            error_msg = f"Timeout calling Retell API for patient {patient.user.email}"
            logger.error(error_msg)
            raise requests.RequestException(error_msg)
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error from Retell API: {e.response.status_code}"
            logger.error(f"{error_msg}. Response: {e.response.text}")
            raise requests.RequestException(f"{error_msg}: {e.response.text}")
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Request error calling Retell API for patient {patient.user.email}: {str(e)}"
            logger.error(error_msg)
            raise
            
        except Exception as e:
            error_msg = f"Unexpected error creating call for patient {patient.user.email}: {str(e)}"
            logger.error(error_msg)
            raise
    
    def get_call_details(self, call_id: str) -> Dict[str, Any]:
        """
        Retrieve call details from Retell API.
        
        Args:
            call_id: Retell call ID
            
        Returns:
            Dictionary containing call details
            
        Raises:
            requests.RequestException: If API call fails
        """
        logger.info(f"Retrieving call details for call ID: {call_id}")
        
        try:
            response = requests.get(
                f"{self.base_url}/get-call/{call_id}",
                headers=self.headers,
                timeout=30
            )
            
            response.raise_for_status()
            call_details = response.json()
            
            logger.info(f"Successfully retrieved call details for: {call_id}")
            return call_details
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Error retrieving call details for {call_id}: {str(e)}"
            logger.error(error_msg)
            raise
    
    def process_webhook_data(self, webhook_data: Dict[str, Any]) -> Optional[RetellCallSession]:
        """
        Process webhook data from Retell and update call session.
        
        Args:
            webhook_data: Webhook payload from Retell
            
        Returns:
            Updated RetellCallSession instance or None if not found
        """
        call_id = webhook_data.get('call_id')
        if not call_id:
            logger.error("No call_id in webhook data")
            return None
        
        logger.info(f"Processing webhook data for call ID: {call_id}")
        
        try:
            # Find the call session
            call_session = RetellCallSession.objects.get(retell_call_id=call_id)
            
            # Update call session with webhook data
            if 'call_status' in webhook_data:
                call_session.call_status = webhook_data['call_status']
            
            if 'start_timestamp' in webhook_data:
                call_session.start_timestamp = webhook_data['start_timestamp']
            
            if 'end_timestamp' in webhook_data:
                call_session.end_timestamp = webhook_data['end_timestamp']
            
            if 'duration_ms' in webhook_data:
                call_session.duration_ms = webhook_data['duration_ms']
            
            if 'transcript' in webhook_data:
                call_session.transcript = webhook_data['transcript']
            
            if 'recording_url' in webhook_data:
                call_session.recording_url = webhook_data['recording_url']
            
            call_session.save()
            
            logger.info(f"Call session updated successfully for call ID: {call_id}")
            return call_session
            
        except RetellCallSession.DoesNotExist:
            logger.error(f"Call session not found for call ID: {call_id}")
            return None
        
        except Exception as e:
            logger.error(f"Error processing webhook data for call ID {call_id}: {str(e)}")
            return None


class GeminiSummaryService:
    """Service for processing transcripts with Gemini AI"""
    
    def __init__(self):
        """Initialize the Gemini service with API configuration"""
        self.api_key = getattr(settings, 'GEMINI_API_KEY', None)
        self.model_name = "gemini-2.5-flash"
        
        if not self.api_key:
            logger.error("GEMINI_API_KEY not configured in settings")
            raise ValueError("Gemini API key not configured")
        
        if genai is None:
            logger.error("google-generativeai library not installed")
            raise ImportError("google-generativeai library is required")
        
        # Configure the Gemini API
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
        
        logger.info("GeminiSummaryService initialized successfully")
    
    def generate_summary(self, transcript: str, patient_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate a comprehensive summary of the call transcript using Gemini AI.
        
        Args:
            transcript: The call transcript text
            patient_context: Optional patient context information
            
        Returns:
            Dictionary containing structured summary data
            
        Raises:
            ValueError: If transcript is empty or invalid
            Exception: If AI processing fails
        """
        if not transcript or not transcript.strip():
            raise ValueError("Transcript is required and cannot be empty")
        
        logger.info("Generating summary for transcript")
        
        # Prepare patient context information
        patient_info = ""
        if patient_context:
            patient_name = patient_context.get('patient_name', 'Patient')
            patient_info = f"Patient Name: {patient_name}\n"
        
        # Create the prompt for summary generation
        prompt = f"""
You are a healthcare AI assistant analyzing a phone call transcript between a healthcare provider and a patient. 
Please provide a comprehensive analysis in the following JSON format:

{patient_info}
Call Transcript:
{transcript}

Please analyze this transcript and provide a response in the following JSON format:
{{
    "summary": "A concise 2-3 sentence overview of the call",
    "key_points": [
        "List of important discussion points",
        "Patient responses and concerns",
        "Health updates or changes mentioned"
    ],
    "health_metrics": {{
        "pain_level": "If mentioned, scale of 1-10 or description",
        "medication_compliance": "true/false/unknown if discussed",
        "mood": "patient's emotional state if apparent",
        "symptoms": "any symptoms mentioned",
        "concerns": "any health concerns raised"
    }},
    "concerning_flags": [
        "Any emergency indicators",
        "Signs of health deterioration",
        "Urgent medical needs"
    ],
    "confidence_score": 0.95
}}

Focus on healthcare-relevant information and maintain patient confidentiality. If certain information is not available in the transcript, use "unknown" or "not mentioned" as appropriate.
"""
        
        try:
            # Generate content using Gemini
            response = self.model.generate_content(prompt)
            
            if not response.text:
                raise Exception("Empty response from Gemini API")
            
            logger.debug(f"Raw Gemini response: {response.text}")
            
            # Parse the JSON response
            try:
                # Clean the response text to extract JSON
                response_text = response.text.strip()
                
                # Remove markdown code blocks if present
                if response_text.startswith('```json'):
                    response_text = response_text[7:]
                if response_text.startswith('```'):
                    response_text = response_text[3:]
                if response_text.endswith('```'):
                    response_text = response_text[:-3]
                
                response_text = response_text.strip()
                
                # Parse JSON
                summary_data = json.loads(response_text)
                
                # Validate required fields
                required_fields = ['summary', 'key_points', 'health_metrics', 'concerning_flags', 'confidence_score']
                for field in required_fields:
                    if field not in summary_data:
                        logger.warning(f"Missing field '{field}' in Gemini response, adding default")
                        if field == 'summary':
                            summary_data[field] = "Summary generation incomplete"
                        elif field in ['key_points', 'concerning_flags']:
                            summary_data[field] = []
                        elif field == 'health_metrics':
                            summary_data[field] = {}
                        elif field == 'confidence_score':
                            summary_data[field] = 0.5
                
                # Ensure confidence score is within valid range
                if not isinstance(summary_data['confidence_score'], (int, float)) or \
                   summary_data['confidence_score'] < 0 or summary_data['confidence_score'] > 1:
                    summary_data['confidence_score'] = 0.5
                
                logger.info("Summary generated successfully")
                return summary_data
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response from Gemini: {e}")
                logger.error(f"Raw response: {response.text}")
                
                # Return fallback summary
                return {
                    'summary': f"Call transcript processed but summary parsing failed: {str(e)}",
                    'key_points': ["Raw transcript available for manual review"],
                    'health_metrics': {},
                    'concerning_flags': ["Summary parsing failed - manual review recommended"],
                    'confidence_score': 0.1
                }
                
        except Exception as e:
            logger.error(f"Error generating summary with Gemini: {str(e)}")
            
            # Return fallback summary for any processing errors
            return {
                'summary': f"Transcript processing failed: {str(e)}",
                'key_points': ["AI processing unavailable - raw transcript stored"],
                'health_metrics': {},
                'concerning_flags': ["AI processing failed - manual review required"],
                'confidence_score': 0.0
            }
    
    def extract_health_metrics(self, transcript: str) -> Dict[str, Any]:
        """
        Extract structured health metrics from the transcript.
        
        Args:
            transcript: The call transcript text
            
        Returns:
            Dictionary containing extracted health metrics
        """
        if not transcript or not transcript.strip():
            logger.warning("Empty transcript provided for health metrics extraction")
            return {}
        
        logger.info("Extracting health metrics from transcript")
        
        prompt = f"""
Analyze this healthcare call transcript and extract specific health metrics in JSON format:

Transcript:
{transcript}

Please extract health metrics and return ONLY a JSON object with the following structure:
{{
    "pain_level": "1-10 scale or description if mentioned, otherwise null",
    "medication_compliance": "true/false/unknown based on discussion",
    "mood": "patient's emotional state description",
    "symptoms": ["list", "of", "symptoms", "mentioned"],
    "vital_signs": {{
        "blood_pressure": "if mentioned",
        "heart_rate": "if mentioned",
        "temperature": "if mentioned",
        "weight": "if mentioned"
    }},
    "concerns": ["list", "of", "health", "concerns"],
    "follow_up_needed": "true/false based on discussion",
    "medication_changes": ["any", "medication", "changes", "discussed"]
}}

Only include metrics that are explicitly mentioned or can be reasonably inferred from the transcript.
"""
        
        try:
            response = self.model.generate_content(prompt)
            
            if not response.text:
                logger.error("Empty response from Gemini for health metrics extraction")
                return {}
            
            # Clean and parse JSON response
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            health_metrics = json.loads(response_text)
            logger.info("Health metrics extracted successfully")
            return health_metrics
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse health metrics JSON: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error extracting health metrics: {str(e)}")
            return {}
    
    def identify_concerning_flags(self, transcript: str) -> List[str]:
        """
        Identify concerning responses or red flags in the transcript.
        
        Args:
            transcript: The call transcript text
            
        Returns:
            List of concerning flags or issues identified
        """
        if not transcript or not transcript.strip():
            logger.warning("Empty transcript provided for concerning flags identification")
            return []
        
        logger.info("Identifying concerning flags in transcript")
        
        prompt = f"""
Analyze this healthcare call transcript and identify any concerning responses, red flags, or urgent medical needs.

Transcript:
{transcript}

Look for:
- Emergency medical situations
- Signs of health deterioration
- Mentions of severe pain or distress
- Medication non-compliance issues
- Suicidal or self-harm ideation
- Confusion or cognitive issues
- Urgent symptoms requiring immediate attention
- Patient expressing inability to care for themselves

Return ONLY a JSON array of concerning flags found:
[
    "Description of concerning flag 1",
    "Description of concerning flag 2"
]

If no concerning flags are identified, return an empty array: []
"""
        
        try:
            response = self.model.generate_content(prompt)
            
            if not response.text:
                logger.error("Empty response from Gemini for concerning flags identification")
                return []
            
            # Clean and parse JSON response
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            concerning_flags = json.loads(response_text)
            
            # Ensure it's a list
            if not isinstance(concerning_flags, list):
                logger.warning("Concerning flags response is not a list, converting")
                concerning_flags = []
            
            logger.info(f"Identified {len(concerning_flags)} concerning flags")
            return concerning_flags
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse concerning flags JSON: {e}")
            return ["JSON parsing error - manual review recommended"]
        except Exception as e:
            logger.error(f"Error identifying concerning flags: {str(e)}")
            return [f"Error in AI analysis: {str(e)} - manual review recommended"]