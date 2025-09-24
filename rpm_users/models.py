from django.db import models
import uuid
from django.contrib.auth.models import User
from datetime import date
import sendgrid
from sendgrid.helpers.mail import Mail
from django.conf import settings
from rpm.secrets import SENDGRID_API_KEY
# Create your models here.
class Patient(models.Model):
    SEX_CHOICES = (('Male', 'Male'), ('Female', 'Female'), ('Others', 'Others'),)
    MONITORING_CHOICES = (('Blood Pressure', 'Blood Pressure'), ('Heart Rate', 'Heart Rate'), ('SPO2', 'SPO2'),("Temperature", "Temperature"),)
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    height = models.DecimalField(blank=True, null=True, max_digits=10, decimal_places=2)
    weight = models.DecimalField(blank=True, null=True, max_digits=10, decimal_places=2)
    insurance = models.CharField(blank=True, null=True, max_length=255)
    insurance_number = models.CharField(blank=True, null=True, max_length=255)
    sex = models.CharField(blank=True, max_length=10, null=True, choices=SEX_CHOICES)
    bmi = models.DecimalField(blank=True, max_digits=10, decimal_places=2, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    monitoring_parameters = models.CharField(blank=True, max_length=20, null=True, choices=MONITORING_CHOICES)
    device_serial_number = models.BigIntegerField(null=True, blank=True, unique=True)
    pharmacy_info = models.TextField(blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    smoke = models.CharField(choices=(('YES', 'YES'), ('NO', 'NO'),), default='NO', max_length=3)
    drink = models.CharField(choices=(('YES', 'YES'), ('NO', 'NO'),), default='NO', max_length=3)
    family_history = models.TextField(null=True, blank=True)
    medications = models.TextField(null=True, blank=True)
    # Address and emergency contact information for machine delivery
    home_address = models.TextField(blank=True, null=True, help_text="Complete home address for machine delivery")
    emergency_contact_name = models.CharField(max_length=255, blank=True, null=True, help_text="Emergency contact person name")
    emergency_contact_phone = models.CharField(max_length=15, blank=True, null=True, help_text="Emergency contact phone number")
    emergency_contact_relationship = models.CharField(max_length=100, blank=True, null=True, help_text="Relationship to patient")
    
    # Primary Care Physician information
    primary_care_physician = models.CharField(max_length=255, blank=True, null=True, help_text="Primary Care Physician name")
    primary_care_physician_phone = models.CharField(max_length=15, blank=True, null=True, help_text="Primary Care Physician phone number")
    
    # Kuch kuch information
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    moderator_assigned = models.ForeignKey('Moderator', blank=True, null=True, on_delete=models.SET_NULL, related_name='moderators')
    doctor_escalated = models.ForeignKey('Doctor', blank=True, null=True, on_delete=models.SET_NULL, related_name='escalated_patients')
    is_escalated = models.BooleanField(default=False)
    
    def __str__(self):
        return self.user.email
    
    @property
    def age(self):
        if self.date_of_birth:
            today = date.today()
            age = today.year - self.date_of_birth.year
            # Check if birthday has occurred this year
            if today.month < self.date_of_birth.month or (today.month == self.date_of_birth.month and today.day < self.date_of_birth.day):
                age -= 1
            return age
        return None

    def save(self, *args, **kwargs):
        # if self.height <= 0 or self.weight <= 0:
        #     raise ValueError("Height and weight must be positive numbers.")
        
        # # Convert height from centimeters to meters for BMI calculation
        # height_in_meters = self.height / 100  # Convert cm to m
        # self.bmi = self.weight / (height_in_meters ** 2)  # Calculate BMI

        is_new = self._state.adding
        # Auto-assign moderator with least patients if not already assigned
        if is_new and not self.moderator_assigned:
            from django.db.models import Count
            from rpm_users.models import Moderator
            moderator = Moderator.objects.annotate(num_patients=models.Count('moderators')).order_by('num_patients').first()
            if moderator:
                self.moderator_assigned = moderator
        super().save(*args, **kwargs)
        if is_new:
            self.send_signup_notification()
    
    # Make it using django signals also send the email to the patient that his account has been created
    # and also send the email to the admin that a new patient has been registered
    def send_signup_notification(self):
        sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
        message = Mail(
            from_email='marketing@pinksurfing.com',
            to_emails=f'shaiqueljilani@gmail.com',
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
                <li><strong>Home Address:</strong> {self.home_address}</li>
                <li><strong>Emergency Contact:</strong> {self.emergency_contact_name} - {self.emergency_contact_phone} ({self.emergency_contact_relationship})</li>
                <li><strong>Primary Care Physician:</strong> {self.primary_care_physician}</li>
                <li><strong>Primary Care Physician Phone:</strong> {self.primary_care_physician_phone}</li>

            </ul>
            """,
        )        
        try:
            sg.send(message)
        except Exception as e:
            print("SendGrid error:", e)

class PastMedicalHistory(models.Model):
    PMH_CHOICES = ((
        ('ARDS', 'Acute Respiratory Distress Syndrome'),
        ('ADHD', 'Attention-Deficit/Hyperactivity Disorder'),
        ('ALS', 'Amyotrophic Lateral Sclerosis'),
        ('ASD', 'Autism Spectrum Disorder'),
        ('AF', 'Atrial Fibrillation'),
        ('BPH', 'Benign Prostatic Hyperplasia'),
        ('BrCa', 'Breast Cancer'),
        ('CVA', 'Cerebrovascular Accident (Stroke)'),
        ('CHAR','Charcot'),
        ('CKD', 'Chronic Kidney Disease'),
        ('COPD', 'Chronic Obstructive Pulmonary Disease'),
        ('CCa', 'Colon Cancer'),
        ('CRPS', 'Complex Regional Pain Syndrome'),
        ('CHF', 'Congestive Heart Failure'),
        ('CAD', 'Coronary Artery Disease'),
        ('DKA', 'Diabetic Ketoacidosis'),
        ('DMK',' Diabetic nephropathy (kidney)'),
        ('DMN','Diabetic neuropathy'),
        ('DMR','Diabetic retinopathy'),
        ('DM', 'Diabetes Mellitus'),
        ('ESRD', 'End Stage Renal Disease'),
        ('GCa', 'Gastric Cancer'),
        ('GERD', 'Gastroesophageal Reflux Disease'),
        ('GAD', 'Generalized Anxiety Disorder'),
        ('GBS', 'Guillain-Barré Syndrome'),
        ('HLH', 'Hemophagocytic Lymphohistiocytosis'),
        ('HUS', 'Hemolytic Uremic Syndrome'),
        ('HSP', 'Henoch-Schönlein Purpura'),
        ('HIV', 'Human Immunodeficiency Virus'),
        ('Hyca', 'Hypercapnea'),
        ('HLD', 'Hyperlipidemia'),
        ('Hpxa', 'Hypoxia'),
        ('HTN', 'Hypertension'),
        ('ITP', 'Idiopathic Thrombocytopenic Purpura'),
        ('LCa', 'Lung Cancer'),
        ('MDD', 'Major Depressive Disorder'),
        ('MI', 'Myocardial Infarction'),
        ('MG', 'Myasthenia Gravis'),
        ('N/A', 'N/A'),
        ('NMO', 'Neuromyelitis Optica'),
        ('OA', 'Osteoarthritis'),
        ('OvCa', 'Ovarian Cancer'),
        ('PCa', 'Pancreatic Cancer'),
        ('PKU', 'Phenylketonuria'),
        ('Peff', 'Pleural Effusion'),
        ('PNA', 'Pneumonia'),
        ('POTS', 'Postural Orthostatic Tachycardia Syndrome'),
        ('PTSD', 'Post-Traumatic Stress Disorder'),
        ('PrCa', 'Prostate Cancer'),
        ('RA', 'Rheumatoid Arthritis'),
        ('SCID', 'Severe Combined Immunodeficiency'),
        ('SCa', 'Skin Cancer'),
        ('OSA','Sleep apnea'),
        ('SMA', 'Spinal Muscular Atrophy'),
        ('SLE', 'Systemic Lupus Erythematosus'),
        ('TeCa', 'Testicular Cancer'),
        ('TCa', 'Thyroid Cancer'),
        ('TTP', 'Thrombotic Thrombocytopenic Purpura'),
        ('TIA', 'Transient Ischemic Attack'),
        ('TB', 'Tuberculosis'),
        ('UTI', 'Urinary Tract Infection'),
        ('URI', 'Upper Respiratory Infection'),
    ))
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_history')
    pmh = models.CharField(choices=PMH_CHOICES, default="N/A", max_length=100)
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    
    def __str__(self) -> str:
        return f"{self.patient.user.email} --- past medical history"


class Moderator(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    def __str__(self):
        return self.user.username


class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    specialization = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    def __str__(self):
        return self.user.username


class Interest(models.Model):
    """Model to store interest leads for RPM services"""
    SERVICE_CHOICES = (
        ('blood_pressure', 'Blood Pressure Monitoring'),
        ('heart_rate', 'Heart Rate Monitoring'),
        ('oxygen', 'Oxygen Saturation(O₂)'),
        ('diabetes', 'Diabetes Management'),
    )
    
    # Personal information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    date_of_birth = models.DateField()
    age = models.IntegerField(blank=True, null=True)
    
    # Medical information
    allergies = models.TextField(blank=True, null=True)
    insurance = models.CharField(max_length=255)
    
    # Service interest
    service_interest = models.CharField(max_length=20, choices=SERVICE_CHOICES)
    
    # Device usage questions
    good_eyesight = models.BooleanField(default=False)
    can_follow_instructions = models.BooleanField(default=False)
    can_take_readings = models.BooleanField(default=False)
    
    # Additional info
    additional_comments = models.TextField(blank=True, null=True)
    
    # Metadata
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.email}"
    
    def save(self, *args, **kwargs):
        # Calculate age if date of birth is provided
        if self.date_of_birth and not self.age:
            today = date.today()
            age = today.year - self.date_of_birth.year
            if today.month < self.date_of_birth.month or (today.month == self.date_of_birth.month and today.day < self.date_of_birth.day):
                age -= 1
            self.age = age
        
        super().save(*args, **kwargs)


class InterestPastMedicalHistory(models.Model):
    """Store past medical history for interest leads"""
    interest = models.ForeignKey(Interest, on_delete=models.CASCADE, related_name='medical_history')
    pmh = models.CharField(choices=PastMedicalHistory.PMH_CHOICES, max_length=100)
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    
    def __str__(self):
        return f"{self.interest.email} - {self.pmh}"


class InterestLead(models.Model):
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    # past_medical_history = models.TextField(blank=True, null=True)
    service_interest = models.CharField(max_length=50, blank=True, null=True)
    insurance = models.CharField(max_length=255, blank=True, null=True)
    # good_eyesight = models.BooleanField(default=False)
    # can_follow_instructions = models.BooleanField(default=False)
    # can_take_readings = models.BooleanField(default=False)
    additional_comments = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    session_key = models.CharField(max_length=64, blank=True, null=True, db_index=True)
    
    # Conversion tracking fields
    is_converted = models.BooleanField(default=False)
    converted_patient = models.ForeignKey(Patient, null=True, blank=True, on_delete=models.SET_NULL)
    converted_at = models.DateTimeField(null=True, blank=True)
    converted_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    
    @property
    def completion_percentage(self):
        """Calculate how complete the lead data is based on filled fields"""
        total_fields = 10  # Total number of relevant fields for completion
        filled_fields = 0
        
        # Check each field and count filled ones
        if self.first_name:
            filled_fields += 1
        if self.last_name:
            filled_fields += 1
        if self.email:
            filled_fields += 1
        if self.phone_number:
            filled_fields += 1
        if self.date_of_birth:
            filled_fields += 1
        if self.age:
            filled_fields += 1
        if self.allergies:
            filled_fields += 1
        if self.service_interest:
            filled_fields += 1
        if self.insurance:
            filled_fields += 1
        if self.additional_comments:
            filled_fields += 1
            
        return round((filled_fields / total_fields) * 100, 1)
    
    @property
    def is_complete(self):
        """Check if lead has all required fields for patient conversion"""
        required_fields = [
            self.first_name,
            self.last_name,
            self.email,
            self.phone_number,
            self.date_of_birth,
            self.insurance
        ]
        return all(field for field in required_fields)
    
    def __str__(self):
        name = f"{self.first_name or ''} {self.last_name or ''}".strip()
        if name:
            return f"{name} - {self.email or 'No email'}"
        return f"Lead {self.id} - {self.email or 'No email'}"


class ModeratorShortcut(models.Model):
    """Model to store personal text shortcuts for moderators"""
    moderator = models.ForeignKey(Moderator, on_delete=models.CASCADE, related_name='shortcuts')
    shortcut_key = models.CharField(max_length=50, help_text="The shortcut key (e.g., '.pe')")
    description = models.CharField(max_length=255, help_text="Brief description of the shortcut")
    content = models.TextField(help_text="The full text content that replaces the shortcut")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['moderator', 'shortcut_key']
        ordering = ['shortcut_key']
    
    def __str__(self):
        return f"{self.moderator.user.username} - {self.shortcut_key}"
