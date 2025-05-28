from django.db import models
import uuid
from django.contrib.auth.models import User
from datetime import date
import sendgrid
from sendgrid.helpers.mail import Mail
from django.conf import settings

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
    
    # Kuch kuch information
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    moderator_assigned = models.ForeignKey('Moderator', blank=True, null=True, on_delete=models.SET_NULL, related_name='moderators')
    
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
        super().save(*args, **kwargs)
        if is_new:
            self.send_signup_notification()

    def send_signup_notification(self):
        sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        message = Mail(
            from_email='marketing@pinksurfing.com',
            to_emails='saishankarpunna@gmail.com',
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
        except Exception as e:
            print("SendGrid error:", e)

class PastMedicalHistory(models.Model):
    PMH_CHOICES = ((
        ('GBS', 'Guillain-Barré Syndrome'),
        ('ALS', 'Amyotrophic Lateral Sclerosis'),
        ('SLE', 'Systemic Lupus Erythematosus'),
        ('ITP', 'Idiopathic Thrombocytopenic Purpura'),
        ('MG', 'Myasthenia Gravis'),
        ('DKA', 'Diabetic Ketoacidosis'),
        ('ARDS', 'Acute Respiratory Distress Syndrome'),
        ('LCa', 'Lung Cancer'),
        ('PCa', 'Pancreatic Cancer'),
        ('CCa', 'Colon Cancer'),
        ('TCa', 'Thyroid Cancer'),
        ('SCa', 'Skin Cancer'),
        ('GCa', 'Gastric Cancer'),
        ('PCa', 'Prostate Cancer'),
        ('TeCa', 'Testicular Cancer'),
        ('BrCa', 'Breast Cancer'),
        ('OvCa', 'Ovarian Cancer'),
        ('TTP', 'Thrombotic Thrombocytopenic Purpura'),
        ('HLH', 'Hemophagocytic Lymphohistiocytosis'),
        ('HSP', 'Henoch-Schönlein Purpura'),
        ('SCID', 'Severe Combined Immunodeficiency'),
        ('PKU', 'Phenylketonuria'),
        ('POTS', 'Postural Orthostatic Tachycardia Syndrome'),
        ('CRPS', 'Complex Regional Pain Syndrome'),
        ('NMO', 'Neuromyelitis Optica'),
        ('HUS', 'Hemolytic Uremic Syndrome'),
        ('SMA', 'Spinal Muscular Atrophy'),
        ('DM', 'Diabetes Mellitus'),
        ('HTN', 'Hypertension'),
        ('AF', 'Atrial Fibrillation'),
        ('CHF', 'Congestive Heart Failure'),
        ('COPD', 'Chronic Obstructive Pulmonary Disease'),
        ('Hpxa', 'Hypoxia'),
        ('Hyca', 'Hypercapnea'),
        ('CKD', 'Chronic Kidney Disease'),
        ('ESRD', 'End Stage Renal Disease'),
        ('GERD', 'Gastroesophageal Reflux Disease'),
        ('OA', 'Osteoarthritis'),
        ('CAD', 'Coronary Artery Disease'),
        ('RA', 'Rheumatoid Arthritis'),
        ('UTI', 'Urinary Tract Infection'),
        ('URI', 'Upper Respiratory Infection'),
        ('BPH', 'Benign Prostatic Hyperplasia'),
        ('HLD', 'Hyperlipidemia'),
        ('TIA', 'Transient Ischemic Attack'),
        ('CVA', 'Cerebrovascular Accident (Stroke)'),
        ('MI', 'Myocardial Infarction'),
        ('PNA', 'Pneumonia'),
        ('TB', 'Tuberculosis'),
        ('HIV', 'Human Immunodeficiency Virus'),
        ('ADHD', 'Attention-Deficit/Hyperactivity Disorder'),
        ('ASD', 'Autism Spectrum Disorder'),
        ('MDD', 'Major Depressive Disorder'),
        ('GAD', 'Generalized Anxiety Disorder'),
        ('PTSD', 'Post-Traumatic Stress Disorder'),
        ('Peff', 'Pleural Effusion'),
        ('N/A', 'N/A'),
    ))
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_history')
    pmh = models.CharField(choices=PMH_CHOICES, default="N/A", max_length=100)
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    
    def __str__(self) -> str:
        return f"{self.patient.user.email} --- past medical history"


class Moderator(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    
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
