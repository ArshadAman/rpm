import os
import sys
import django
from datetime import date
import sendgrid
from sendgrid.helpers.mail import Mail

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rpm.settings')
django.setup()

from django.conf import settings

def send_signup_notification(self):
        sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        message = Mail(
            from_email='marketing@pinksurfing.com',
            to_emails=f'saishankar15052005@gmail.com',
            subject='New RPM Patient Signup Notification',
            html_content=f"""
            <h3>New Patient Registered for RPM</h3>
            <ul>
                <li><strong>Name:</strong> {self.user.first_name} {self.user.last_name}</li>
                <li><strong>Email:</strong> {self.user.email}</li>
                <li><strong>Mobile Number:</strong> {self.phone_number}</li>
                <li><strong>Date of Birth:</strong> {self.date_of_birth}</li>
                <li><strong>Sex:</strong> {self.sex}</li>
                <li><strong>Insurance:</strong> {self.insurance}</li>
                <li><strong>Monitoring Parameters:</strong> {self.monitoring_parameters}</li>
            </ul>
            """,
        )        
        try:
            sg.send(message)
            print("Email sent successfully!")
        except Exception as e:
            print("SendGrid error:", e)

# Test function that simulates a patient for testing email sending
def test_email():
    # Create a mock patient object with all the required attributes
    class MockPatient:
        def __init__(self):
            self.user = type('obj', (object,), {
                'first_name': 'Test',
                'last_name': 'Patient',
                'email': 'test@example.com'
            })
            self.phone_number = '555-123-4567'
            self.date_of_birth = date(1990, 1, 1)
            self.sex = 'Male'
            self.insurance = 'Test Insurance'
            self.monitoring_parameters = 'Blood Pressure'
    
    # Create mock patient and send email
    patient = MockPatient()
    send_signup_notification(patient)

# If this script is run directly, execute the test function
if __name__ == "__main__":
    test_email()
