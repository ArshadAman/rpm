from django import forms
from django.contrib.auth.models import User
from .models import Patient, Moderator, Doctor

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
            'medications',
            'primary_care_physician',
            'primary_care_physician_phone'
        ]

class ModeratorForm(forms.Form):
    """Form for creating and editing moderators"""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter username'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email address'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter first name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter last name'
        })
    )
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter phone number (optional)'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        })
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })
    )

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)
        
        # If editing, populate fields and make password optional
        if self.instance:
            self.fields['username'].initial = self.instance.user.username
            self.fields['email'].initial = self.instance.user.email
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['phone_number'].initial = self.instance.phone_number
            
            # Make password fields optional for editing
            self.fields['password'].required = False
            self.fields['confirm_password'].required = False
            self.fields['password'].help_text = "Leave blank to keep current password"
            self.fields['confirm_password'].help_text = "Leave blank to keep current password"

    def clean_username(self):
        username = self.cleaned_data['username']
        
        # Check for duplicate username (exclude current instance if editing)
        existing_user = User.objects.filter(username=username)
        if self.instance:
            existing_user = existing_user.exclude(id=self.instance.user.id)
        
        if existing_user.exists():
            raise forms.ValidationError("A user with this username already exists.")
        
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        
        # Check for duplicate email (exclude current instance if editing)
        existing_user = User.objects.filter(email=email)
        if self.instance:
            existing_user = existing_user.exclude(id=self.instance.user.id)
        
        if existing_user.exists():
            raise forms.ValidationError("A user with this email already exists.")
        
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        # Only validate password matching if passwords are provided
        if password or confirm_password:
            if password != confirm_password:
                raise forms.ValidationError("Passwords do not match.")
        
        # For new moderators, password is required
        if not self.instance and not password:
            raise forms.ValidationError("Password is required for new moderators.")

        return cleaned_data 


class DoctorForm(forms.Form):
    """Form for creating and editing doctors"""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter username'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email address'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter first name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter last name'
        })
    )
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter phone number (optional)'
        })
    )
    specialization = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter specialization (e.g., Cardiology, Internal Medicine)'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        })
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })
    )

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)
        
        # If editing, populate fields and make password optional
        if self.instance:
            self.fields['username'].initial = self.instance.user.username
            self.fields['email'].initial = self.instance.user.email
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['phone_number'].initial = self.instance.phone_number
            self.fields['specialization'].initial = self.instance.specialization
            
            # Make password fields optional for editing
            self.fields['password'].required = False
            self.fields['confirm_password'].required = False
            self.fields['password'].help_text = "Leave blank to keep current password"
            self.fields['confirm_password'].help_text = "Leave blank to keep current password"

    def clean_username(self):
        username = self.cleaned_data['username']
        
        # Check for duplicate username (exclude current instance if editing)
        existing_user = User.objects.filter(username=username)
        if self.instance:
            existing_user = existing_user.exclude(id=self.instance.user.id)
        
        if existing_user.exists():
            raise forms.ValidationError("A user with this username already exists.")
        
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        
        # Check for duplicate email (exclude current instance if editing)
        existing_user = User.objects.filter(email=email)
        if self.instance:
            existing_user = existing_user.exclude(id=self.instance.user.id)
        
        if existing_user.exists():
            raise forms.ValidationError("A user with this email already exists.")
        
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        # Only validate password matching if passwords are provided
        if password or confirm_password:
            if password != confirm_password:
                raise forms.ValidationError("Passwords do not match.")
        
        # For new doctors, password is required
        if not self.instance and not password:
            raise forms.ValidationError("Password is required for new doctors.")

        return cleaned_data