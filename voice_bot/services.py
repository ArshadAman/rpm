import google.generativeai as genai # type: ignore
import os
from typing import Dict, List, Optional
import json
from django.conf import settings
from django.utils import timezone
from .models import VoiceInteraction, VoiceQuestion, AIKnowledgeBase
from rpm_users.models import Patient
import logging

logger = logging.getLogger(__name__)

class VoiceBotAI:
    """
    AI Brain for the voice bot using Google Gemini
    """
    
    def __init__(self):
        # Configure Gemini API
        api_key = getattr(settings, 'GEMINI_API_KEY', os.getenv('GEMINI_API_KEY'))
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in settings or environment variables")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        
        # Configure generation settings for consistent responses
        self.generation_config = genai.types.GenerationConfig(
            temperature=0.7,
            max_output_tokens=200,
            top_k=40,
            top_p=0.95,
        )
        
        # Configure safety settings for medical use
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
        
    def get_context_for_patient(self, patient: Patient) -> str:
        """Get relevant context about the patient for AI responses"""
        context = f"""
        Patient Information:
        - Name: {patient.user.get_full_name()}
        - Age: {patient.age if hasattr(patient, 'age') else 'Unknown'}
        - Sex: {patient.get_sex_display() if patient.sex else 'Unknown'}
        - Monitoring Parameters: {patient.monitoring_parameters}
        - Medical Conditions: {patient.allergies if patient.allergies else 'None specified'}
        - Current Medications: {patient.medications if patient.medications else 'None specified'}
        
        You are a voice assistant for a Remote Patient Monitoring (RPM) system. 
        Your role is to:
        1. Ask health-related questions and record responses
        2. Answer patient questions about their RPM program
        3. Provide general health guidance (but always refer to doctors for medical advice)
        4. Identify potential emergencies and escalate appropriately
        
        Always be empathetic, professional, and clear in your responses.
        If a patient describes serious symptoms, recommend they contact their doctor immediately.
        """
        return context
    
    def generate_response(self, patient: Patient, patient_input: str, conversation_history: List[Dict] = None) -> str:
        """
        Generate AI response based on patient input and context using Gemini
        """
        try:
            context = self.get_context_for_patient(patient)
            
            # Build conversation prompt for Gemini
            prompt = context + "\n\n"
            
            if conversation_history:
                prompt += "Conversation History:\n"
                for entry in conversation_history[-5:]:  # Last 5 exchanges
                    prompt += f"Patient: {entry.get('patient_input', '')}\n"
                    prompt += f"Assistant: {entry.get('ai_response', '')}\n"
                prompt += "\n"
            
            # Add current input
            prompt += f"Current Patient Input: {patient_input}\n\n"
            prompt += "Please provide a helpful, empathetic response as a voice assistant for RPM. Keep the response conversational and under 200 words:"
            
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error generating AI response with Gemini: {str(e)}")
            return "I apologize, but I'm having trouble processing your request right now. Please try again or contact your healthcare provider if this is urgent."
    
    def analyze_health_concern(self, patient_input: str) -> Dict:
        """
        Analyze patient input for health concerns and urgency using Gemini
        """
        try:
            prompt = f"""
            Analyze the following patient statement for health concerns and provide a JSON response:
            "{patient_input}"
            
            Return ONLY a valid JSON object with this exact structure:
            {{
                "urgency_level": "low|medium|high|emergency",
                "concerns": ["list of identified health concerns"],
                "requires_doctor_contact": true/false,
                "sentiment": "positive|neutral|negative",
                "keywords": ["relevant medical keywords"]
            }}
            
            Guidelines:
            - "emergency": Life-threatening symptoms (chest pain, difficulty breathing, severe bleeding)
            - "high": Serious symptoms requiring prompt medical attention
            - "medium": Concerning symptoms that should be monitored
            - "low": Normal health inquiries or minor concerns
            """
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=150,
                ),
                safety_settings=self.safety_settings
            )
            
            # Parse JSON response
            result = json.loads(response.text.strip())
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON from Gemini health analysis: {str(e)}")
            return {
                "urgency_level": "medium",
                "concerns": ["Unable to analyze - please review manually"],
                "requires_doctor_contact": True,
                "sentiment": "neutral",
                "keywords": []
            }
        except Exception as e:
            logger.error(f"Error analyzing health concern with Gemini: {str(e)}")
            return {
                "urgency_level": "medium",
                "concerns": [],
                "requires_doctor_contact": False,
                "sentiment": "neutral",
                "keywords": []
            }

class VoiceBotQuestionEngine:
    """
    Manages the questions to ask patients during voice calls
    """
    
    def get_questions_for_patient(self, patient: Patient) -> List[VoiceQuestion]:
        """
        Get relevant questions based on patient's condition and history
        """
        questions = VoiceQuestion.objects.filter(is_active=True)
        
        # Filter based on patient's conditions if needed
        # For now, return general health check questions
        return questions.filter(question_type='health_check').order_by('priority')[:5]
    
    def get_next_question(self, interaction: VoiceInteraction) -> Optional[VoiceQuestion]:
        """
        Get the next question to ask in an ongoing interaction
        """
        asked_questions = interaction.questions_asked or []
        available_questions = self.get_questions_for_patient(interaction.patient)
        
        for question in available_questions:
            if question.id not in asked_questions:
                return question
        
        return None

class VoiceBotManager:
    """
    Main manager class that coordinates the voice bot functionality
    """
    
    def __init__(self):
        self.ai_engine = VoiceBotAI()
        self.question_engine = VoiceBotQuestionEngine()
    
    def start_voice_interaction(self, patient: Patient, interaction_type: str = 'outbound_scheduled') -> VoiceInteraction:
        """
        Start a new voice interaction
        """
        interaction = VoiceInteraction.objects.create(
            patient=patient,
            interaction_type=interaction_type,
            phone_number=patient.phone_number,
            call_status='initiated'
        )
        
        return interaction
    
    def process_patient_response(self, interaction: VoiceInteraction, patient_input: str, current_question: str = None) -> Dict:
        """
        Process patient's voice input and generate appropriate response
        """
        # Analyze the input for health concerns
        health_analysis = self.ai_engine.analyze_health_concern(patient_input)
        
        # Generate AI response
        conversation_history = self.get_conversation_history(interaction)
        ai_response = self.ai_engine.generate_response(
            interaction.patient, 
            patient_input, 
            conversation_history
        )
        
        # Update interaction record
        questions = interaction.questions_asked or []
        responses = interaction.patient_responses or []
        ai_responses = interaction.ai_responses or []
        
        if current_question:
            questions.append(current_question)
        responses.append(patient_input)
        ai_responses.append(ai_response)
        
        interaction.questions_asked = questions
        interaction.patient_responses = responses
        interaction.ai_responses = ai_responses
        
        # Update health alerts if needed
        if health_analysis.get('urgency_level') in ['high', 'emergency']:
            alerts = interaction.health_alerts or []
            alerts.append({
                'timestamp': str(interaction.created_at),
                'concern': health_analysis.get('concerns', []),
                'urgency': health_analysis.get('urgency_level')
            })
            interaction.health_alerts = alerts
            interaction.follow_up_required = True
        
        interaction.save()
        
        return {
            'ai_response': ai_response,
            'health_analysis': health_analysis,
            'next_question': self.question_engine.get_next_question(interaction)
        }
    
    def get_conversation_history(self, interaction: VoiceInteraction) -> List[Dict]:
        """
        Get conversation history for context
        """
        questions = interaction.questions_asked or []
        responses = interaction.patient_responses or []
        ai_responses = interaction.ai_responses or []
        
        history = []
        for i in range(min(len(questions), len(responses), len(ai_responses))):
            history.append({
                'question': questions[i],
                'patient_input': responses[i],
                'ai_response': ai_responses[i]
            })
        
        return history
    
    def end_interaction(self, interaction: VoiceInteraction):
        """
        End the voice interaction and perform cleanup
        """
        interaction.call_status = 'completed'
        interaction.ended_at = timezone.now()
        interaction.save()
        
        # Generate summary or alerts if needed
        if interaction.follow_up_required:
            self.create_follow_up_alert(interaction)
    
    def create_follow_up_alert(self, interaction: VoiceInteraction):
        """
        Create follow-up alerts for healthcare providers
        """
        # This could send emails, create tasks, etc.
        # For now, we'll just log it
        logger.info(f"Follow-up required for patient {interaction.patient.user.get_full_name()} after voice interaction {interaction.id}")
