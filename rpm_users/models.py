from django.db import models
import uuid
from django.contrib.auth.models import User
from datetime import date

# Create your models here.
class Patient(models.Model):
    SEX_CHOICES = (('Male', 'Male'), ('Female', 'Female'), ('Others', 'Others'),)
    MONITORING_CHOICES = (('Blood Pressure', 'Blood Pressure'), ('Heart Rate', 'Heart Rate'), ('SPO2', 'SPO2'),("Temperature", "Temperature"),)
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    height = models.DecimalField(blank=True, null=True, max_digits=10, decimal_places=2)
    weight = models.DecimalField(blank=True, null=True, max_digits=10, decimal_places=2)
    insurance = models.CharField(blank=True, null=True, max_length=255)
    sex = models.CharField(blank=True, max_length=10, null=True, choices=SEX_CHOICES)
    bmi = models.DecimalField(blank=True, max_digits=10, decimal_places=2, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    monitoring_parameters = models.CharField(blank=True, max_length=20, null=True, choices=MONITORING_CHOICES)
    device_serial_number = models.IntegerField(null=True, blank=True)
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
    # Ensure height is in meters
    if self.height <= 0 or self.weight <= 0:
        raise ValueError("Height and weight must be positive numbers.")
    
    # Convert height from centimeters to meters for BMI calculation
    height_in_meters = self.height / 100  # Convert cm to m
    self.bmi = self.weight / (height_in_meters ** 2)  # Calculate BMI

    super().save(*args, **kwargs)
    
    
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
