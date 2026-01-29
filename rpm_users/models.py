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
    
    # Status and Sticky Notes for moderator/doctor tracking
    STATUS_CHOICES = (
        ('green', 'Green'),
        ('orange', 'Orange'),
        ('red', 'Red'),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='green', blank=True, null=True)
    sticky_note = models.TextField(max_length=500, blank=True, null=True, help_text="Reminder notes for this patient (max 500 chars)")
    
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
        ('ETOH', 'Alcohol use'),
        ('HGB', 'Anemia'),
        ('AdInsuff', 'Adrenal insufficiency'),
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
        ('ChrPn', 'Chronic Pain'),
        ('Const', 'Constipation'),
        ('CAD', 'Coronary Artery Disease'),
        ('DKA', 'Diabetic Ketoacidosis'),
        ('DJD', 'Degenerative Joint Disease'),
        ('DMK',' Diabetic nephropathy (kidney)'),
        ('DMN','Diabetic neuropathy'),
        ('DMR','Diabetic retinopathy'),
        ('DM', 'Diabetes Mellitus'),
        ('ESRD', 'End Stage Renal Disease'),
        ('Femr', 'Femur Fracture'),
        ('GCa', 'Gastric Cancer'),
        ('GERD', 'Gastroesophageal Reflux Disease'),
        ('GAD', 'Generalized Anxiety Disorder'),
        ('Gitis', 'Gastritis '),
        ('GIB', 'GI bleed'),
        ('GBS', 'Guillain-Barré Syndrome'),
        ('HLH', 'Hemophagocytic Lymphohistiocytosis'),
        ('HUS', 'Hemolytic Uremic Syndrome'),
        ('HUMR', 'Humerus FX'),
        ('HSP', 'Henoch-Schönlein Purpura'),
        ('HIV', 'Human Immunodeficiency Virus'),
        ('Hyca', 'Hypercapnea'),
        ('Hypo', 'Hypotension'),
        ('HpTh', 'Hypothyroidism'),
        ('HLD', 'Hyperlipidemia'),
        ('Hpxa', 'Hypoxia'),
        ('HTN', 'Hypertension'),
        ('Insm', 'Insomnia'),
        ('ILUS', 'Ileus'),
        ('ITP', 'Idiopathic Thrombocytopenic Purpura'),
        ('LCa', 'Lung Cancer'),
        ('MDD', 'Major Depressive Disorder'),
        ('MOB', 'Morbid Obesity'),
        ('MI', 'Myocardial Infarction'),
        ('MG', 'Myasthenia Gravis'),
        ('MVP', 'Mitral Valve Prolapse'),
        ('N/A', 'N/A'),
        ('NMO', 'Neuromyelitis Optica'),
        ('Npathy','Neuropathy'),
        ('OA', 'Osteoarthritis'),
        ('ORTSTATES', 'Orthostatic Hypotension'),
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
        ('SVT', 'Supra Ventricular Tachycardia'),
        ('OSA','Sleep apnea'),
        ('SMA', 'Spinal Muscular Atrophy'),
        ('SLE', 'Systemic Lupus Erythematosus'),
        ('SP STEN', 'Spinal Stenosis'), 
        ('TeCa', 'Testicular Cancer'),
        ('TCa', 'Thyroid Cancer'),
        ('TTP', 'Thrombotic Thrombocytopenic Purpura'),
        ('TIA', 'Transient Ischemic Attack'),
        ('Tachy', 'Tachycardia '),
        ('TB', 'Tuberculosis'),
        ('UTI', 'Urinary Tract Infection'),
        ('URI', 'Upper Respiratory Infection'),
        ('VF', 'Valley Fever'),
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
    sex = models.CharField(max_length=10, blank=True, null=True, choices=Patient.SEX_CHOICES)
    
    # Biometrics
    height = models.DecimalField(blank=True, null=True, max_digits=10, decimal_places=2)
    weight = models.DecimalField(blank=True, null=True, max_digits=10, decimal_places=2)
    
    # Medical information
    allergies = models.TextField(blank=True, null=True)
    insurance = models.CharField(max_length=255)
    insurance_number = models.CharField(max_length=255, blank=True, null=True)
    pharmacy_info = models.TextField(blank=True, null=True)
    medications = models.TextField(null=True, blank=True)
    family_history = models.TextField(null=True, blank=True)
    
    # Lifestyle
    smoke = models.CharField(choices=(('YES', 'YES'), ('NO', 'NO'),), max_length=3, blank=True, null=True)
    drink = models.CharField(choices=(('YES', 'YES'), ('NO', 'NO'),), max_length=3, blank=True, null=True)
    
    # Service interest
    service_interest = models.CharField(max_length=20, choices=SERVICE_CHOICES)
    
    # Device usage questions
    good_eyesight = models.BooleanField(default=False)
    can_follow_instructions = models.BooleanField(default=False)
    can_take_readings = models.BooleanField(default=False)
    device_serial_number = models.CharField(max_length=255, blank=True, null=True)
    
    # Address
    home_address = models.TextField(blank=True, null=True)
    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=255, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True, null=True)
    emergency_contact_relationship = models.CharField(max_length=100, blank=True, null=True)
    
    # Primary Care Physician
    primary_care_physician = models.CharField(max_length=255, blank=True, null=True, help_text="Primary Care Physician name")
    primary_care_physician_phone = models.CharField(max_length=15, blank=True, null=True)
    primary_care_physician_email = models.EmailField(blank=True, null=True)
    
    # Additional info
    additional_comments = models.TextField(blank=True, null=True)
    medical_summary_file = models.FileField(upload_to='medical_summaries/', blank=True, null=True)
    
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
    
    # Additional fields from Excel import
    street_address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=10, blank=True, null=True)
    mrn_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="MRN#")
    phone_number_2 = models.CharField(max_length=20, blank=True, null=True, verbose_name="Phone 2")
    sex = models.CharField(max_length=1, blank=True, null=True, choices=[('M', 'Male'), ('F', 'Female')])
    marital_status = models.CharField(max_length=20, blank=True, null=True)
    primary_insured_id = models.CharField(max_length=50, blank=True, null=True)
    
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
        total_fields = 18  # Total number of relevant fields for completion
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
        if self.street_address:
            filled_fields += 1
        if self.city:
            filled_fields += 1
        if self.zip_code:
            filled_fields += 1
        if self.mrn_number:
            filled_fields += 1
        if self.phone_number_2:
            filled_fields += 1
        if self.sex:
            filled_fields += 1
        if self.marital_status:
            filled_fields += 1
        if self.primary_insured_id:
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
    
    def save(self, *args, **kwargs):
        """Override save to clean phone numbers and skip leads without mobile numbers"""
        from .utils import clean_phone_number
        
        # Skip saving if no mobile number is provided
        if not self.phone_number or not self.phone_number.strip():
            print(f"Skipping lead save - no mobile number provided for {self.first_name} {self.last_name}")
            return  # Skip saving this lead
        
        # Clean phone numbers before saving
        if self.phone_number:
            self.phone_number = clean_phone_number(self.phone_number)
        if self.phone_number_2:
            self.phone_number_2 = clean_phone_number(self.phone_number_2)
        
        super().save(*args, **kwargs)
    
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


class EmailOTP(models.Model):
    """Model to store email OTP verification codes for patient registration"""
    email = models.EmailField()
    otp_code = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"OTP for {self.email} - {self.otp_code}"
    
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at


class Video(models.Model):
    """Model to store YouTube video links for landing page display"""
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    title = models.CharField(max_length=255, help_text="Video title to display")
    youtube_url = models.URLField(max_length=500, help_text="YouTube video URL (watch, embed, or short link)")
    description = models.TextField(blank=True, null=True, help_text="Brief description of the video")
    order = models.IntegerField(default=0, help_text="Display order (lower numbers appear first)")
    is_active = models.BooleanField(default=True, help_text="Whether to show on landing page")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='videos_created')
    
    class Meta:
        ordering = ['order', '-created_at']
    
    def __str__(self):
        return self.title
    
    def get_embed_url(self):
        """Convert various YouTube URL formats to embed URL (W3Schools simple approach)"""
        import re
        
        if not self.youtube_url:
            return None
        
        # Clean the URL - remove any extra parameters that might cause issues
        url = self.youtube_url.strip()
        
        # Extract video ID from all YouTube URL formats (including Shorts)
        patterns = [
            r'youtube\.com\/shorts\/([a-zA-Z0-9_-]{11})',  # Shorts
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',  # Regular
            r'youtube\.com\/watch\?.*[?&]v=([a-zA-Z0-9_-]{11})',  # Watch with params
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                video_id = match.group(1)
                # Use youtube-nocookie.com for better privacy and fewer restrictions
                # This sometimes helps with embedding issues
                return f"https://www.youtube-nocookie.com/embed/{video_id}"
        
        return None
    
    def get_thumbnail_url(self):
        """Get YouTube video thumbnail URL"""
        import re
        
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/shorts\/([a-zA-Z0-9_-]{11})',  # YouTube Shorts
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.youtube_url)
            if match:
                video_id = match.group(1)
                return f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        
        return None
    
    def is_youtube_short(self):
        """Check if the video is a YouTube Short"""
        import re
        return bool(re.search(r'youtube\.com\/shorts\/', self.youtube_url))


class Testimonial(models.Model):
    """Model to store customer testimonials/reviews for landing page display"""
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    customer_name = models.CharField(max_length=255, help_text="Customer's name to display")
    customer_image = models.ImageField(upload_to='testimonials/', blank=True, null=True, help_text="Customer's photo")
    review_text = models.TextField(help_text="Customer's review/testimonial text")
    rating = models.IntegerField(default=5, choices=[(i, f"{i} Stars") for i in range(1, 6)], help_text="Rating out of 5 stars")
    location = models.CharField(max_length=100, blank=True, null=True, help_text="Customer's location (e.g., 'New York, NY')")
    order = models.IntegerField(default=0, help_text="Display order (lower numbers appear first)")
    is_active = models.BooleanField(default=True, help_text="Whether to show on landing page")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='testimonials_created')
    
    class Meta:
        ordering = ['order', '-created_at']
    
    def __str__(self):
        return f"{self.customer_name} - {self.rating} stars"
    
    def get_image_url(self):
        """Get the image URL or return a default placeholder"""
        if self.customer_image:
            return self.customer_image.url
        return None


class LabDocument(models.Model):
    """Model to store lab documents uploaded by labs"""
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    patient_name = models.CharField(max_length=255, help_text="Name of the patient")
    document = models.FileField(upload_to='lab_documents/', help_text="Uploaded lab document")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.patient_name} - {self.uploaded_at.strftime('%Y-%m-%d')}"


# Labs Models
class LabCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name_plural = "Lab Categories"

    def __str__(self):
        return self.name

class LabTest(models.Model):
    category = models.ForeignKey(LabCategory, on_delete=models.CASCADE, related_name='tests')
    name = models.CharField(max_length=100)
    unit = models.CharField(max_length=50, blank=True, null=True)
    min_range = models.CharField(max_length=50, blank=True, null=True)
    max_range = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.category.name})"

class LabResult(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='lab_results')
    test = models.ForeignKey(LabTest, on_delete=models.CASCADE, related_name='results')
    value = models.CharField(max_length=255)
    date_recorded = models.DateTimeField()
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    file = models.FileField(upload_to='lab_reports/', blank=True, null=True)
    file_url = models.URLField(max_length=500, blank=True, null=True)  # Cloudinary URL
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_recorded']

    def __str__(self):
        return f"{self.patient} - {self.test.name}: {self.value}"