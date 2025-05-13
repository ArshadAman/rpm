from django.db import models
import uuid

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
