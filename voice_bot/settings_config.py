# Voice Bot Configuration for Django Settings

# Add these to your main settings.py file

# Voice Bot Settings
import os
VOICE_BOT_ENABLED = True

# Google Gemini API Settings
GEMINI_API_KEY =os.getenv('GEMINI_API_KEY')  # Get from https://makersuite.google.com/app/apikey

# Twilio Settings
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')  # Get from Twilio Console
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')    # Get from Twilio Console
TWILIO_PHONE_NUMBER = '+1234567890'  # Your Twilio phone number

# Base URL for webhooks (must be HTTPS in production)
BASE_URL = 'https://yourdomain.com'  # Change to your actual domain

# Celery Settings for Voice Bot Tasks
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# Celery Beat Schedule for Voice Bot
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'schedule-voice-calls': {
        'task': 'voice_bot.tasks.schedule_voice_calls',
        'schedule': crontab(minute='*/15'),  # Run every 15 minutes
    },
    'analyze-voice-interactions': {
        'task': 'voice_bot.tasks.analyze_voice_interactions',
        'schedule': crontab(hour=2, minute=0),  # Run daily at 2 AM
    },
}

# Add voice_bot to INSTALLED_APPS
INSTALLED_APPS = [
    # ... your existing apps ...
    'voice_bot',
    'celery',
]

# Logging configuration for voice bot
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'voice_bot_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'voice_bot.log',
        },
    },
    'loggers': {
        'voice_bot': {
            'handlers': ['voice_bot_file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Voice Bot AI Settings
VOICE_BOT_AI_MODEL = 'gpt-4'  # or 'gpt-3.5-turbo' for lower cost
VOICE_BOT_MAX_CALL_DURATION = 300  # 5 minutes max call duration
VOICE_BOT_QUESTION_TIMEOUT = 30  # 30 seconds timeout for each question

# Emergency Alert Settings
EMERGENCY_ALERT_PHONE_NUMBERS = ['+1234567890']  # Phone numbers to call for emergencies
EMERGENCY_ALERT_EMAILS = ['doctor@example.com']  # Email addresses for emergency alerts
