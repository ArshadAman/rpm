from celery import shared_task
from django.conf import settings
import sendgrid
from sendgrid.helpers.mail import Mail
import logging
from django.apps import apps

logger = logging.getLogger(__name__)

@shared_task
def send_new_lead_notification(lead_id, model_name='InterestLead'):
    """
    Asynchronously send a lead notification email to the admin using Celery.
    Handles both Interest and InterestLead models.
    """
    try:
        # Dynamically get the model
        LeadModel = apps.get_model('rpm_users', model_name)
        lead = LeadModel.objects.get(id=lead_id)
        
        ADMIN_EMAIL = "shaiqueljilani@gmail.com"
        FROM_EMAIL = "marketing@pinksurfing.com"
        
        # Prepare data (handle differences between Interest and InterestLead)
        first_name = lead.first_name or 'N/A'
        last_name = lead.last_name or 'N/A'
        email = lead.email or 'N/A'
        phone = lead.phone_number or 'N/A'
        service = getattr(lead, 'service_interest', 'N/A')
        city = getattr(lead, 'city', 'N/A')
        address = getattr(lead, 'street_address', getattr(lead, 'home_address', 'N/A'))
        
        channel = "Web Form" if model_name == 'Interest' else "AI Call/Manual"
        
        # Build professional HTML content
        html_content = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 10px; }}
                    .header {{ background-color: #7928CA; color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center; }}
                    .header h1 {{ margin: 0; font-size: 24px; }}
                    .badge {{ display: inline-block; background: #fff; color: #7928CA; padding: 2px 10px; border-radius: 15px; font-size: 12px; margin-top: 5px; font-weight: bold; }}
                    .section {{ padding: 20px; border: 1px solid #f0f0f0; border-top: none; }}
                    .info-row {{ display: flex; margin-bottom: 10px; border-bottom: 1px solid #f9f9f9; padding-bottom: 5px; }}
                    .info-label {{ font-weight: bold; width: 150px; color: #7928CA; }}
                    .info-value {{ flex: 1; }}
                    .footer {{ text-align: center; font-size: 12px; color: #888; margin-top: 20px; padding: 10px; }}
                    .btn {{ display: inline-block; background-color: #7928CA; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; margin-top: 20px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎯 New Lead Received</h1>
                        <span class="badge">Source: {channel}</span>
                    </div>
                    <div class="section">
                        <div class="info-row">
                            <span class="info-label">Name</span>
                            <span class="info-value">{first_name} {last_name}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Email</span>
                            <span class="info-value">{email}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Phone</span>
                            <span class="info-value">{phone}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Interest</span>
                            <span class="info-value">{str(service).replace('_', ' ').title()}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">City</span>
                            <span class="info-value">{city}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Address</span>
                            <span class="info-value">{address}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Insurance</span>
                            <span class="info-value">{getattr(lead, 'insurance', 'N/A')}</span>
                        </div>
                        
                        <div style="margin-top: 20px; padding: 15px; background: #fdf6ff; border-radius: 5px;">
                            <strong>Additional Comments:</strong><br>
                            {lead.additional_comments or 'None'}
                        </div>

                        <div style="text-align: center;">
                            <p style="font-size: 14px; color: #666;">View lead in the admin dashboard for full clinical conversion.</p>
                        </div>
                    </div>
                    <div class="footer">
                        <p>This is an automated asynchronous notification via Celery.</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        if not settings.SENDGRID_API_KEY:
            logger.error("SENDGRID_API_KEY not found in settings.")
            return

        sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        message = Mail(
            from_email=FROM_EMAIL,
            to_emails=ADMIN_EMAIL,
            subject=f"🚀 New {channel} Lead: {first_name} {last_name}",
            html_content=html_content
        )
        
        sg.send(message)
        logger.info(f"Asynchronous lead notification sent for {model_name} {lead_id}")
        
    except Exception as e:
        logger.error(f"Celery lead notification failed for {model_name} {lead_id}: {str(e)}")
