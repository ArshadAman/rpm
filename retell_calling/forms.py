from django import forms
from .models import FacilityLead


class FacilityLeadExcelUploadForm(forms.Form):
    """Form for uploading Excel file with facility leads"""
    excel_file = forms.FileField(
        label='Upload Excel File',
        help_text='Upload an Excel file (.xlsx, .xls) or CSV with facility information',
        required=True,
        widget=forms.FileInput(attrs={
            'accept': '.xlsx,.xls,.csv',
            'class': 'form-control',
            'id': 'facility_excel_upload'
        })
    )

    def clean_excel_file(self):
        """Validate the uploaded file"""
        excel_file = self.cleaned_data.get('excel_file')
        
        if excel_file:
            # Check file size (max 5MB)
            if excel_file.size > 5 * 1024 * 1024:
                raise forms.ValidationError('File size must not exceed 5MB.')
            
            # Check file type
            if not excel_file.name.lower().endswith(('.xlsx', '.xls', '.csv')):
                raise forms.ValidationError('Please upload a valid Excel (.xlsx, .xls) or CSV file.')
        
        return excel_file


class FacilityLeadFilterForm(forms.Form):
    """Form for filtering facility leads"""
    search = forms.CharField(
        required=False,
        label='Search',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by facility name, city, or phone number'
        })
    )
    
    category = forms.CharField(
        required=False,
        label='Category',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Filter by category'
        })
    )
    
    city = forms.CharField(
        required=False,
        label='City',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Filter by city'
        })
    )
    
    CALL_STATUS_CHOICES = [
        ('', 'All'),
        ('called', 'Called'),
        ('not_called', 'Not Called'),
    ]
    
    call_status = forms.ChoiceField(
        required=False,
        label='Call Status',
        choices=CALL_STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    EMAIL_STATUS_CHOICES = [
        ('', 'All'),
        ('sent', 'Email Sent'),
        ('not_sent', 'Email Not Sent'),
    ]
    
    email_status = forms.ChoiceField(
        required=False,
        label='Email Status',
        choices=EMAIL_STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
