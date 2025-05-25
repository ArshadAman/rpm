from django.db import models
import uuid
from django.conf import settings
from twilio.rest import Client

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
        # First save the model
        super().save(*args, **kwargs)
        
        # Check for critical health parameters
        critical_conditions = []
        
        # Check heart rate
        try:
            if self.heart_rate:
                heart_rate = int(self.heart_rate)
                if heart_rate > 110:
                    critical_conditions.append(f"Heart rate is {heart_rate} (above 110)")
        except (ValueError, TypeError):
            pass

        # Check systolic blood pressure
        try:
            if self.systolic_blood_pressure:
                systolic_bp = int(self.systolic_blood_pressure)
                if systolic_bp > 170:
                    critical_conditions.append(f"Systolic blood pressure is {systolic_bp} (above 170)")
        except (ValueError, TypeError):
            pass

        # Check oxygen saturation
        try:
            if self.spo2:
                spo2 = int(self.spo2)
                if spo2 < 88:
                    critical_conditions.append(f"Oxygen saturation is {spo2} (below 88)")
        except (ValueError, TypeError):
            pass

        # Send SMS alert if there are critical conditions
        if critical_conditions and settings.ADMIN_PHONE_NUMBER:
            print("critical_conditions", f"ALERT: Critical health parameters detected for patient {self.patient.user.first_name} {self.patient.user.last_name}:\n" + 
                         "\n".join(critical_conditions))
            try:
                client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                message = client.messages.create(
                    body=f"ALERT: Critical health parameters detected for patient {self.patient.user.first_name} {self.patient.user.last_name}:\n" + 
                         "\n".join(critical_conditions),
                    from_=settings.TWILIO_PHONE_NUMBER,
                    to=settings.ADMIN_PHONE_NUMBER
                )
                print("message", message)
                print(f"SMS alert sent successfully. Message SID: {message.sid}")
            except Exception as e:
                print(f"Failed to send SMS alert: {str(e)}")

class Documentation(models.Model):
    TITLE_CHOICES = (
        ('RPM Progress Note', 'RPM Progress Note'),
        ('Progress Note', 'Progress Note'),
    )
    patient = models.ForeignKey('rpm_users.Patient', on_delete=models.CASCADE, related_name='documentations', blank=True, null=True)
    title = models.CharField(max_length=255, choices=TITLE_CHOICES, default="Progress Note")
    history_of_present_illness = models.TextField()
    chief_complaint = models.TextField(max_length=255, blank=True, null=True)
    subjective = models.TextField(blank=True, null=True)
    objective = models.TextField(max_length=255, blank=True, null=True)
    assessment = models.TextField(max_length=255, blank=True, null=True)
    plan = models.TextField(max_length=255, blank=True, null=True)
    file = models.FileField(upload_to='documentations/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # If chief_complaint is not provided, fetch it from the patient's monitoring parameters
        if not self.chief_complaint and self.report and self.report.patient:
            self.chief_complaint = f"Monitoring for {self.report.patient.monitoring_parameters}"
            
        # If objective is not provided, fetch the last 3 reports of the patient
        if not self.objective and self.report and self.report.patient:
            # Get the last 3 reports for this patient, excluding the current report
            last_reports = Reports.objects.filter(
                patient=self.report.patient
            ).exclude(
                id=self.report.id
            ).order_by('-created_at')[:3]
            
            if last_reports:
                objective_text = "Previous Reports:\n"
                for i, prev_report in enumerate(last_reports, 1):
                    objective_text += f"{i}. {prev_report.created_at.strftime('%Y-%m-%d %H:%M')}:\n"
                    if prev_report.blood_pressure:
                        objective_text += f"   BP: {prev_report.blood_pressure}\n"
                    if prev_report.heart_rate:
                        objective_text += f"   HR: {prev_report.heart_rate}\n"
                    if prev_report.spo2:
                        objective_text += f"   SpO2: {prev_report.spo2}\n"
                    if prev_report.temperature:
                        objective_text += f"   Temp: {prev_report.temperature}\n"
                    if prev_report.symptoms:
                        objective_text += f"   Symptoms: {prev_report.symptoms}\n"
                    objective_text += "\n"
                
                self.objective = objective_text
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.title} - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
