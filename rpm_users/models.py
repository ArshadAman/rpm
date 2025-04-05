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
    monitoring_parameters = models.CharField(blank=True, max_length=20, null=True, choices=MONITORING_CHOICES)
    device_serial_number = models.IntegerField(null=True, blank=True)
    pharmacy_info = models.TextField(blank=True, null=True)
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


class Moderator(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self):
        return self.user.username
