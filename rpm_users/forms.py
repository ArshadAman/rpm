from django import forms
from .models import Patient

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = [
            'date_of_birth',
            'height',
            'weight',
            'insurance',
            'sex',
            'phone_number',
            'monitoring_parameters',
            'device_serial_number',
            'pharmacy_info',
            'allergies',
            'drink',
            'smoke',
            'family_history',
            'medications'
        ] 