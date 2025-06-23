# Voice Bot for RPM System

This intelligent voice bot system enables automated voice calls to patients for health monitoring and provides AI-powered responses to patient questions.

## Features

🎙️ **Proactive Calling**: Automatically calls patients on schedules
🧠 **AI Brain**: Uses Google Gemini to answer patient questions intelligently
📊 **Health Monitoring**: Asks predefined health questions and records responses
🚨 **Emergency Detection**: Identifies urgent health concerns and alerts providers
📱 **Twilio Integration**: Professional voice calling capabilities
⏰ **Flexible Scheduling**: Daily, weekly, monthly, or custom call schedules
📈 **Analytics**: Track patient interactions and health trends

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Settings

Add to your `settings.py`:

```python
# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ... existing apps ...
    'voice_bot',
    'celery',
]

# Voice Bot Configuration
GEMINI_API_KEY = 'your-gemini-api-key'  # Get from https://makersuite.google.com/app/apikey
TWILIO_ACCOUNT_SID = 'your-twilio-account-sid'
TWILIO_AUTH_TOKEN = 'your-twilio-auth-token'
TWILIO_PHONE_NUMBER = '+1234567890'
BASE_URL = 'https://yourdomain.com'

# Celery Configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

from celery.schedules import crontab
CELERY_BEAT_SCHEDULE = {
    'schedule-voice-calls': {
        'task': 'voice_bot.tasks.schedule_voice_calls',
        'schedule': crontab(minute='*/15'),
    },
}
```

### 3. Update URLs

Add to your main `urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    # ... existing patterns ...
    path('voice-bot/', include('voice_bot.urls')),
]
```

### 4. Run Migrations

```bash
python manage.py makemigrations voice_bot
python manage.py migrate
```

### 5. Populate Sample Data

```bash
python manage.py populate_voice_bot
```

### 6. Set Up External Services

#### Twilio Setup:
1. Create account at https://twilio.com
2. Get Account SID and Auth Token from Console
3. Purchase a phone number
4. Configure webhooks pointing to your server

#### Google Gemini Setup:
1. Create account at https://makersuite.google.com
2. Generate API key
3. Add to settings

#### Redis Setup:
```bash
# Install Redis
sudo apt-get install redis-server
# Or use Docker
docker run -d -p 6379:6379 redis
```

### 7. Start Services

```bash
# Start Django
python manage.py runserver

# Start Celery Worker (in new terminal)
celery -A rpm worker --loglevel=info

# Start Celery Beat (in new terminal)
celery -A rpm beat --loglevel=info
```

## Usage

### Access Voice Bot Dashboard
Visit: `http://localhost:8000/voice-bot/dashboard/`

### Schedule Patient Calls
1. Go to dashboard
2. Click "Schedule" for a patient
3. Set frequency and preferred time
4. Save schedule

### Manual Call Initiation
1. Go to dashboard
2. Click "Call Now" for any patient
3. Call will be initiated immediately

### View Interaction History
1. Click "View History" for a patient
2. See all past voice interactions
3. Review conversation transcripts

## API Endpoints

- `POST /voice-bot/initiate-call/<patient_id>/` - Start manual call
- `GET /voice-bot/api/patient-summary/<patient_id>/` - Get patient voice summary
- `POST /voice-bot/api/emergency-alert/` - Create emergency alert

## How It Works

### Call Flow:
1. **Celery scheduler** triggers calls based on patient schedules
2. **Twilio** initiates voice call to patient
3. **Voice bot** asks predefined health questions
4. **Patient responds** via voice
5. **Twilio** converts speech to text
6. **Google Gemini** processes response and generates reply
7. **Twilio** converts reply to speech and plays to patient
8. **Django** stores full conversation in database

### AI Features:
- Contextual responses based on patient medical history
- Emergency detection in patient responses
- Sentiment analysis of patient mood
- Automated follow-up recommendations

## Customization

### Adding New Questions:
```python
from voice_bot.models import VoiceQuestion

VoiceQuestion.objects.create(
    question_type='health_check',
    question_text='How is your pain level today?',
    expected_response_type='scale_1_10',
    priority=1
)
```

### Adding Knowledge Base:
```python
from voice_bot.models import AIKnowledgeBase

AIKnowledgeBase.objects.create(
    knowledge_type='faq',
    title='What to do about side effects?',
    content='Contact your doctor if you experience...',
    keywords=['side effects', 'medication', 'doctor']
)
```

## Monitoring & Analytics

### Dashboard Features:
- Real-time call status
- Patient interaction history
- Follow-up alerts
- Health trend analysis

### Admin Interface:
- Voice interaction management
- Question bank editing
- Call schedule management
- Knowledge base updates

## Security & Compliance

- All voice data encrypted
- HIPAA-compliant storage
- Secure webhook endpoints
- Patient consent tracking

## Troubleshooting

### Common Issues:

1. **Calls not working**:
   - Check Twilio credentials
   - Verify webhook URLs are accessible
   - Ensure HTTPS in production

2. **AI responses poor**:
   - Verify Gemini API key
   - Check knowledge base content
   - Review conversation context

3. **Scheduled calls not running**:
   - Ensure Celery beat is running
   - Check Redis connection
   - Verify timezone settings

### Logs:
- Check `voice_bot.log` for detailed logs
- Monitor Celery worker output
- Review Twilio webhook logs

## Production Deployment

### Requirements:
- HTTPS domain (required by Twilio)
- Redis server
- Celery workers
- Production-grade database

### Environment Variables:
```bash
export GEMINI_API_KEY="your-key"
export TWILIO_ACCOUNT_SID="your-sid"
export TWILIO_AUTH_TOKEN="your-token"
export TWILIO_PHONE_NUMBER="+1234567890"
export BASE_URL="https://youromain.com"
```

## Support

For issues or feature requests, check the Django admin interface or contact your development team.
