# Gemini AI Configuration for Voice Bot
# Add these settings to your main Django settings.py

import os
from django.core.exceptions import ImproperlyConfigured

# Gemini API Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not GEMINI_API_KEY:
    raise ImproperlyConfigured(
        "GEMINI_API_KEY environment variable is required. "
        "Get your API key from https://makersuite.google.com/app/apikey"
    )

# Gemini Model Settings
GEMINI_MODEL_NAME = 'gemini-pro'
GEMINI_TEMPERATURE = 0.7
GEMINI_MAX_OUTPUT_TOKENS = 200
GEMINI_TOP_K = 40
GEMINI_TOP_P = 0.95

# Safety Settings for Medical Use Case
GEMINI_SAFETY_SETTINGS = [
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

# Voice Bot Specific Settings
VOICE_BOT_AI_RESPONSE_MAX_LENGTH = 200
VOICE_BOT_CONVERSATION_HISTORY_LIMIT = 5
VOICE_BOT_DEFAULT_LANGUAGE = 'en-US'

# Health Analysis Settings
HEALTH_ANALYSIS_TEMPERATURE = 0.3
HEALTH_ANALYSIS_MAX_TOKENS = 150

# Emergency Keywords (can be used for immediate escalation)
EMERGENCY_KEYWORDS = [
    'chest pain', 'can\'t breathe', 'difficulty breathing', 'severe bleeding',
    'unconscious', 'heart attack', 'stroke', 'suicide', 'overdose',
    'severe pain', 'emergency', 'call 911', 'ambulance'
]
