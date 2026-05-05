"""Email service for sending lead notifications via SendGrid"""
import sendgrid
from sendgrid.helpers.mail import Mail
from django.conf import settings
from rpm.secrets import SENDGRID_API_KEY
import logging

logger = logging.getLogger(__name__)

LEAD_NOTIFICATION_EMAIL = "shaiqueljilani@gmail.com"
FROM_EMAIL = "marketing@pinksurfing.com"


def send_lead_notification_email(lead_data: dict, channel: str):
    """
    Send a lead notification email to the admin.
    
    Args:
        lead_data: Dictionary containing lead information with fields like:
                   first_name, last_name, email, phone_number, service_interest, etc.
        channel: Source channel - either "express_interest_form" or "inbound_call"
    """
    # Check if lead has minimum required data to send email
    # We need at least name or email to send meaningful notification
    has_name = lead_data.get('first_name') or lead_data.get('last_name')
    has_contact = lead_data.get('email') or lead_data.get('phone_number')
    
    if not (has_name or has_contact):
        logger.debug("Skipping lead notification email - insufficient lead data")
        return None
    
    try:
        # Extract relevant fields
        first_name = lead_data.get('first_name') or 'N/A'
        last_name = lead_data.get('last_name') or 'N/A'
        email = lead_data.get('email') or 'N/A'
        phone_number = lead_data.get('phone_number') or 'N/A'
        date_of_birth = lead_data.get('date_of_birth') or 'N/A'
        sex = lead_data.get('sex') or 'N/A'
        insurance = lead_data.get('insurance') or 'N/A'
        service_interest = lead_data.get('service_interest') or 'N/A'
        allergies = lead_data.get('allergies') or 'N/A'
        medications = lead_data.get('medications') or 'N/A'
        
        # Additional fields for InterestLead (inbound calls)
        street_address = lead_data.get('street_address') or lead_data.get('home_address') or 'N/A'
        city = lead_data.get('city') or 'N/A'
        zip_code = lead_data.get('zip_code') or 'N/A'
        
        # Contact information
        emergency_contact_name = lead_data.get('emergency_contact_name') or 'N/A'
        emergency_contact_phone = lead_data.get('emergency_contact_phone') or 'N/A'
        emergency_contact_relationship = lead_data.get('emergency_contact_relationship') or 'N/A'
        primary_care_physician = lead_data.get('primary_care_physician') or 'N/A'
        primary_care_physician_phone = lead_data.get('primary_care_physician_phone') or 'N/A'
        
        # Additional info
        additional_comments = lead_data.get('additional_comments') or 'N/A'
        
        # Format channel display
        channel_display = "Express Interest Form" if channel == "express_interest_form" else "Inbound Call"
        
        # Build HTML email content
        html_content = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 800px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }}
                    .header {{ background-color: #007bff; color: white; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                    .header h1 {{ margin: 0; font-size: 24px; }}
                    .channel-badge {{ display: inline-block; background-color: #28a745; color: white; padding: 5px 10px; border-radius: 3px; font-size: 12px; font-weight: bold; margin-top: 10px; }}
                    .section {{ margin-bottom: 25px; }}
                    .section-title {{ background-color: #f0f0f0; padding: 10px; font-weight: bold; font-size: 14px; border-left: 4px solid #007bff; margin-bottom: 10px; }}
                    .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }}
                    .info-item {{ padding: 8px; background-color: #f9f9f9; border-radius: 3px; }}
                    .info-label {{ font-weight: bold; color: #007bff; font-size: 12px; text-transform: uppercase; }}
                    .info-value {{ margin-top: 3px; }}
                    .full-width {{ grid-column: 1 / -1; }}
                    .footer {{ background-color: #f0f0f0; padding: 10px; text-align: center; font-size: 12px; color: #666; border-top: 1px solid #ddd; margin-top: 20px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎯 New Lead Received</h1>
                        <div class="channel-badge">{channel_display}</div>
                    </div>
                    
                    <div class="section">
                        <div class="section-title">Personal Information</div>
                        <div class="info-grid">
                            <div class="info-item">
                                <div class="info-label">First Name</div>
                                <div class="info-value">{first_name}</div>
                            </div>
                            <div class="info-item">
                                <div class="info-label">Last Name</div>
                                <div class="info-value">{last_name}</div>
                            </div>
                            <div class="info-item">
                                <div class="info-label">Email</div>
                                <div class="info-value">{email}</div>
                            </div>
                            <div class="info-item">
                                <div class="info-label">Phone Number</div>
                                <div class="info-value">{phone_number}</div>
                            </div>
                            <div class="info-item">
                                <div class="info-label">Date of Birth</div>
                                <div class="info-value">{date_of_birth}</div>
                            </div>
                            <div class="info-item">
                                <div class="info-label">Sex</div>
                                <div class="info-value">{sex}</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="section">
                        <div class="section-title">Address Information</div>
                        <div class="info-grid">
                            <div class="info-item full-width">
                                <div class="info-label">Street Address</div>
                                <div class="info-value">{street_address}</div>
                            </div>
                            <div class="info-item">
                                <div class="info-label">City</div>
                                <div class="info-value">{city}</div>
                            </div>
                            <div class="info-item">
                                <div class="info-label">Zip Code</div>
                                <div class="info-value">{zip_code}</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="section">
                        <div class="section-title">Medical Information</div>
                        <div class="info-grid">
                            <div class="info-item">
                                <div class="info-label">Insurance Provider</div>
                                <div class="info-value">{insurance}</div>
                            </div>
                            <div class="info-item">
                                <div class="info-label">Service Interest</div>
                                <div class="info-value">{service_interest}</div>
                            </div>
                            <div class="info-item full-width">
                                <div class="info-label">Allergies</div>
                                <div class="info-value">{allergies}</div>
                            </div>
                            <div class="info-item full-width">
                                <div class="info-label">Medications</div>
                                <div class="info-value">{medications}</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="section">
                        <div class="section-title">Emergency Contact</div>
                        <div class="info-grid">
                            <div class="info-item">
                                <div class="info-label">Name</div>
                                <div class="info-value">{emergency_contact_name}</div>
                            </div>
                            <div class="info-item">
                                <div class="info-label">Phone</div>
                                <div class="info-value">{emergency_contact_phone}</div>
                            </div>
                            <div class="info-item">
                                <div class="info-label">Relationship</div>
                                <div class="info-value">{emergency_contact_relationship}</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="section">
                        <div class="section-title">Primary Care Physician</div>
                        <div class="info-grid">
                            <div class="info-item">
                                <div class="info-label">Name</div>
                                <div class="info-value">{primary_care_physician}</div>
                            </div>
                            <div class="info-item">
                                <div class="info-label">Phone</div>
                                <div class="info-value">{primary_care_physician_phone}</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="section">
                        <div class="section-title">Additional Comments</div>
                        <div class="info-grid">
                            <div class="info-item full-width">
                                <div class="info-value">{additional_comments}</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="footer">
                        <p>This is an automated email notification. Please do not reply to this email.</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        # Create and send email
        message = Mail(
            from_email=FROM_EMAIL,
            to_emails=LEAD_NOTIFICATION_EMAIL,
            subject=f"🎯 New {channel_display} Lead: {first_name} {last_name}",
            html_content=html_content,
        )
        
        sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
        response = sg.send(message)
        
        logger.info(f"Lead notification email sent to {LEAD_NOTIFICATION_EMAIL} for lead: {first_name} {last_name}")
        return response
        
    except Exception as e:
        logger.error(f"Error sending lead notification email: {str(e)}")
        # Don't raise exception - we don't want email failure to break lead creation
        return None
