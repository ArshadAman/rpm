from django.db import models

# Create your models here.
class Reports(models.Model):
    patient = models.ForeignKey('rpm_users.Patient', on_delete=models.CASCADE, related_name='reports')
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
        ()
    )
    report = models.ForeignKey(Reports, on_delete=models.CASCADE, related_name='documentations')
    title = models.CharField(max_length=255)
    description = models.TextField()
    cheif_complaint = models.TextField(max_length=255, blank=True, null=True)
    subjective = models.TextField(max_length=255, blank=True, null=True)
    objective = models.TextField(max_length=255, blank=True, null=True)
    assessment = models.TextField(max_length=255, blank=True, null=True)
    plan = models.TextField(max_length=255, blank=True, null=True)
    file = models.FileField(upload_to='documentations/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title