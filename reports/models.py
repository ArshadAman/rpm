from django.db import models
import uuid
import sendgrid
from sendgrid.helpers.mail import Mail
from rpm.secrets import SENDGRID_API_KEY
# Create your models here.
class Reports(models.Model):
    patient = models.ForeignKey('rpm_users.Patient', on_delete=models.CASCADE, related_name='reports')
    # Common fields
    device_id = models.CharField(max_length=64, blank=True, null=True)
    created_at_device = models.CharField(max_length=64, blank=True, null=True)
    data_type = models.CharField(max_length=64, blank=True, null=True)
    imei = models.CharField(max_length=32, blank=True, null=True)
    iccid = models.CharField(max_length=32, blank=True, null=True)
    serial_number = models.CharField(max_length=32, blank=True, null=True)
    model_number = models.CharField(max_length=32, blank=True, null=True)
    is_test = models.CharField(max_length=8, blank=True, null=True)
    # Sphygmomanometer specific
    user_id = models.CharField(max_length=32, blank=True, null=True)
    systolic_blood_pressure = models.CharField(max_length=8, blank=True, null=True)
    diastolic_blood_pressure = models.CharField(max_length=8, blank=True, null=True)
    pulse = models.CharField(max_length=8, blank=True, null=True)
    irregular_heartbeat = models.CharField(max_length=8, blank=True, null=True)
    hand_shaking = models.CharField(max_length=8, blank=True, null=True)
    triple_mode = models.CharField(max_length=8, blank=True, null=True)
    battery_level = models.CharField(max_length=8, blank=True, null=True)
    signal_strength = models.CharField(max_length=8, blank=True, null=True)
    measurement_timestamp = models.CharField(max_length=32, blank=True, null=True)
    timezone = models.CharField(max_length=16, blank=True, null=True)
    # Blood Glucose Meter specific
    blood_glucose = models.CharField(max_length=16, blank=True, null=True)
    glucose_unit = models.CharField(max_length=8, blank=True, null=True)
    test_paper_type = models.CharField(max_length=8, blank=True, null=True)
    sample_type = models.CharField(max_length=8, blank=True, null=True)
    meal_mark = models.CharField(max_length=8, blank=True, null=True)
    signal_level = models.CharField(max_length=8, blank=True, null=True)
    measurement_timezone = models.CharField(max_length=16, blank=True, null=True)
    upload_timestamp = models.CharField(max_length=32, blank=True, null=True)
    upload_timezone = models.CharField(max_length=16, blank=True, null=True)
    # Old fields for compatibility
    blood_pressure = models.CharField(max_length=10, blank=True, null=True)
    heart_rate = models.CharField(max_length=10, blank=True, null=True)
    spo2 = models.CharField(max_length=10, blank=True, null=True)
    temperature = models.CharField(max_length=10, blank=True, null=True)
    symptoms = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f'{self.patient.user.first_name} {self.patient.user.last_name} - {self.created_at.strftime("%Y-%m-%d %H:%M:%S")}'
    
    def save(self, *args, **kwargs):
        # Check if this is a new record (not yet saved)
        is_new = self.pk is None
        
        # Save the model first
        super().save(*args, **kwargs)
        
        # If this is a new record, check the vitals
        if is_new:
            self.check_vitals_and_send_alert()
    
    def check_vitals_and_send_alert(self):
        """Check if any vital signs are outside safe ranges and send an alert if needed"""
        alert_needed = False
        alert_reasons = []
        
        # Check heart rate (pulse) - above 110 is concerning
        if self.pulse and int(self.pulse) > 110:
            alert_needed = True
            alert_reasons.append(f"Heart Rate: {self.pulse} bpm (above 110)")
        # Check systolic blood pressure - above 170 is concerning
        if self.systolic_blood_pressure and int(self.systolic_blood_pressure) > 170:
            alert_needed = True
            alert_reasons.append(f"Systolic BP: {self.systolic_blood_pressure} mmHg (above 170)")
        
        # Check oxygen saturation - below 88 is concerning
        if self.spo2 and int(self.spo2) < 88:
            alert_needed = True
            alert_reasons.append(f"Oxygen Saturation: {self.spo2}% (below 88%)")
        
        # If any vital signs are outside safe ranges, send an alert
        if alert_needed:
            self.send_alert_email(alert_reasons)
    
    def send_alert_email(self, alert_reasons):
        """Send an email alert to the admin about concerning vital signs"""
        try:
            sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
            message = Mail(
                from_email='marketing@pinksurfing.com',
                to_emails='shaiqueljilani@gmail.com',  # Admin email
                subject='ALERT: Abnormal Vital Signs Detected',
                html_content=f"""
                <h3>Abnormal Vital Signs Alert</h3>
                <p>The following patient has reported vital signs outside the normal range:</p>
                
                <ul>
                    <li><strong>Patient:</strong> {self.patient.user.first_name} {self.patient.user.last_name}</li>
                    <li><strong>Email:</strong> {self.patient.user.email}</li>
                    <li><strong>Mobile Number:</strong> {self.patient.phone_number}</li>
                    <li><strong>Date of Birth:</strong> {self.patient.date_of_birth}</li>
                </ul>
                
                <h4>Concerning Vital Signs:</h4>
                <ul>
                    {''.join(f'<li><strong>{reason}</strong></li>' for reason in alert_reasons)}
                </ul>
                
                <p>This reading was taken at: {self.measurement_timestamp or self.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
                
                <p>Please review this patient's data and take appropriate action.</p>
                """,
            )
            
            sg.send(message)
            print(f"Alert email sent for patient {self.patient.user.first_name} {self.patient.user.last_name}")
        except Exception as e:
            print(f"SendGrid error: {e}")
    
class Documentation(models.Model):
    TITLE_CHOICES = (
        ('CCM Initial Note', 'CCM Initial Note'),
        ('CCM Note Clinical Staff', 'CCM Note Clinical Staff'),
        ('CCM Note NP/PA', 'CCM Note NP/PA'),
        ('CCM Note Physician', 'CCM Note Physician'),
        ('CCM-HTN Progress Note', 'CCM-HTN Progress Note'),
        ('E-Visit Followup Note MD', 'E-Visit Followup Note MD'),
        ('E-Visit Followup Note MD NP/PA', 'E-Visit Followup Note MD NP/PA'),
        ('E-Visit Followup Note NP/PA', 'E-Visit Followup Note NP/PA'), 
        ('Inpatient Hospital H&P Physician', 'Inpatient Hospital H&P Physician'),
        ('Occupation Therapy Note', 'Occupation Therapy Note'),
        ('Office Visit Note MD', 'Office Visit Note MD'),
        ('Office Visit Note NP/PA', 'Office Visit Note NP/PA'),
        ('Physical Therapy Note', 'Physical Therapy Note'),
        ('Progress Note', 'Progress Note'),
        ('Rehabilitation MD Note', 'Rehabilitation MD Note'),
        ('RPM Note Clinical Staff', 'RPM Note Clinical Staff'),
        ('RPM Progress Note', 'RPM Progress Note'),
        ('Skilled Nursing Consult', 'Skilled Nursing Consult'),
        ('Skilled Nursing H&P', 'Skilled Nursing H&P'),
        ('Skilled Nursing Note', 'Skilled Nursing Note'),
        ('Speech Therapy Note', 'Speech Therapy Note'),
        ('Telehealth Initial Visit Physician', 'Telehealth Initial Visit Physician'),
        ('Telehealth Visit NP/PA', 'Telehealth Visit NP/PA'),
        ('Telehealth Visit Physician', 'Telehealth Visit Physician'),
        ('Telephone Visit Initiated By Patient', 'Telephone Visit Initiated By Patient'),
        ('Transitional Care Note NP/PA', 'Transitional Care Note NP/PA'),
        ('Transitional Care Note Physician', 'Transitional Care Note Physician'),
    )
    patient = models.ForeignKey('rpm_users.Patient', on_delete=models.CASCADE, related_name='documentations', blank=True, null=True)
    title = models.CharField(max_length=255, choices=TITLE_CHOICES, default="Progress Note")
    history_of_present_illness = models.TextField()
    chief_complaint = models.TextField(max_length=255, blank=True, null=True)
    subjective = models.TextField(blank=True, null=True)
    objective = models.TextField(max_length=255, blank=True, null=True)
    assessment = models.TextField(max_length=255, blank=True, null=True)
    written_by = models.TextField(max_length=255, blank=True, null=True)
    plan = models.TextField(max_length=255, blank=True, null=True)
    file = models.FileField(upload_to='documentations/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Patient snapshot fields for documentation
    doc_patient_name = models.CharField(max_length=255, blank=True, null=True)
    doc_dob = models.DateField(blank=True, null=True)
    doc_sex = models.CharField(max_length=10, blank=True, null=True)
    doc_monitoring_params = models.CharField(max_length=255, blank=True, null=True)
    doc_clinical_staff = models.CharField(max_length=255, blank=True, null=True)
    doc_moderator = models.CharField(max_length=255, blank=True, null=True)
    doc_report_date = models.DateField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.title} - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
