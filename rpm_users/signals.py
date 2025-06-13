from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.conf import settings
from django.template.loader import render_to_string
import sendgrid
from sendgrid.helpers.mail import Mail
from .models import Doctor, Patient, Moderator
import logging

logger = logging.getLogger(__name__)

# Remove the User signal and replace with specific model signals
@receiver(post_save, sender=Doctor)
def send_doctor_creation_email(sender, instance, created, **kwargs):
    """Send welcome email when a Doctor profile is created."""
    if created and instance.user and instance.user.email:
        send_welcome_email(instance.user, 'doctor')

@receiver(post_save, sender=Moderator)
def send_moderator_creation_email(sender, instance, created, **kwargs):
    """Send welcome email when a Moderator profile is created."""
    if created and instance.user and instance.user.email:
        send_welcome_email(instance.user, 'moderator')

@receiver(post_save, sender=Patient)
def send_patient_creation_email(sender, instance, created, **kwargs):
    """Send welcome email when a Patient profile is created."""
    if created and instance.user and instance.user.email:
        send_welcome_email(instance.user, 'patient')

def send_welcome_email(user, user_type):
    """
    Send a customized welcome email based on user type.
    """
    try:
        # Skip email sending if no SendGrid API key is configured
        if not hasattr(settings, 'SENDGRID_API_KEY') or not settings.SENDGRID_API_KEY:
            logger.warning(f"SendGrid not configured. Skipping welcome email for {user.email}")
            return
        
        # Get email template and subject based on user type
        template_name, subject, email_context = get_email_template_data(user, user_type)
        
        # Render HTML email
        html_message = render_to_string(template_name, email_context)
        
        # Use SendGrid to send email
        sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        message = Mail(
            from_email='marketing@pinksurfing.com',
            to_emails=user.email,
            subject=subject,
            html_content=html_message
        )
        
        # Send email
        sg.send(message)
        
        logger.info(f"Welcome email sent successfully to {user.email} ({user_type})")
        
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")

def get_email_template_data(user, user_type):
    """
    Get the appropriate email template, subject, and context based on user type.
    """
    base_context = {
        'user': user,
        'first_name': user.first_name or 'User',
        'last_name': user.last_name or '',
        'email': user.email,
        'site_name': 'RPM - Remote Patient Monitoring',
        'support_email': 'support@pinksurfing.com',
        'company_name': 'RPM Healthcare',
    }
    
    if user_type == 'doctor':
        return (
            'emails/doctor_welcome.html',
            f'Welcome to RPM - Your Doctor Account is Ready, Dr. {user.last_name or user.first_name}',
            {
                **base_context,
                'user_type': 'Doctor',
                'role_description': 'Healthcare Provider',
                'dashboard_url': '/doctor-login/',
                'features': [
                    'View and manage escalated patients',
                    'Access detailed patient medical histories',
                    'Receive real-time patient alerts',
                    'Collaborate with healthcare teams',
                ],
                'next_steps': [
                    'Log in to your doctor dashboard',
                    'Review your assigned patient cases',
                    'Set up your notification preferences',
                    'Complete your medical profile',
                ]
            }
        )
    
    elif user_type == 'moderator':
        return (
            'emails/moderator_welcome.html',
            f'Welcome to RPM - Your Moderator Account is Active, {user.first_name}',
            {
                **base_context,
                'user_type': 'Moderator',
                'role_description': 'Healthcare Moderator',
                'dashboard_url': '/moderator-login/',
                'features': [
                    'Manage patient registrations and assignments',
                    'Monitor patient compliance and data',
                    'Escalate cases to appropriate doctors',
                    'Generate comprehensive reports',
                ],
                'next_steps': [
                    'Access your moderator dashboard',
                    'Review pending patient registrations',
                    'Set up monitoring parameters',
                    'Configure escalation protocols',
                ]
            }
        )
    
    else:  # patient
        return (
            'emails/patient_welcome.html',
            f'Welcome to RPM - Your Remote Monitoring Journey Begins, {user.first_name}',
            {
                **base_context,
                'user_type': 'Patient',
                'role_description': 'Remote Monitoring Patient',
                'dashboard_url': '/patient-login/',
                'features': [
                    'Track your health metrics in real-time',
                    'Receive personalized care recommendations',
                    'Communicate with your healthcare team',
                    'Access your medical history and reports',
                ],
                'next_steps': [
                    'Complete your health profile setup',
                    'Connect your monitoring devices',
                    'Schedule your first virtual consultation',
                    'Download the RPM mobile app',
                ]
            }
        )
