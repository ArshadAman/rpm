from django.db import models
import uuid

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
    
class Documentation(models.Model):
    TITLE_CHOICES = (
        ('RPM Progress Note', 'RPM Progress Note'),
        ('CCN-HTN Progress Note', 'CCN-HTN Progress Note'),
        ('Progress Note', 'Progress Note'),
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
