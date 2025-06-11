from django import forms
from .models import Documentation, Reports

class DocumentationForm(forms.ModelForm):
    # Renamed field in the form for clarity, mapping to history_of_present_illness in the model
    full_documentation = forms.CharField(widget=forms.Textarea(attrs={'rows': 15, 'placeholder': 'Enter full documentation'}))
    
    # Patient snapshot fields
    doc_patient_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Patient Name'}))
    doc_dob = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    doc_sex = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Sex'}))
    doc_monitoring_params = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Monitoring Parameters'}))
    doc_clinical_staff = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Clinical Staff'}))
    doc_moderator = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Moderator'}))
    doc_report_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Documentation
        fields = [
            "title",
            "full_documentation",
            "doc_patient_name",
            "doc_dob",
            "doc_sex",
            "doc_monitoring_params",
            "doc_clinical_staff",
            "doc_moderator",
            "doc_report_date",
        ]
        # Removed widgets for individual fields
        # widgets = {
        #     "history_of_present_illness": forms.Textarea(attrs={"rows": 3}),
        #     "chief_complaint": forms.Textarea(attrs={"rows": 2}),
        #     "subjective": forms.Textarea(attrs={"rows": 2}),
        #     "objective": forms.Textarea(attrs={"rows": 2}),
        #     "assessment": forms.Textarea(attrs={"rows": 2}),
        #     "plan": forms.Textarea(attrs={"rows": 2}),
        # }

    # Map the form field 'full_documentation' to the model field 'history_of_present_illness'
    # This mapping logic is now handled in the view to set written_by and explicitly save history_of_present_illness
    # def clean_full_documentation(self):
    #     return self.cleaned_data['full_documentation']

    # Custom save method to handle saving the full documentation and setting written_by
    def save(self, commit=True, user=None):
        instance = super().save(commit=False)
        instance.history_of_present_illness = self.cleaned_data['full_documentation']
        # Set other individual fields to None or empty string if they are no longer used
        instance.chief_complaint = ""
        instance.subjective = ""
        instance.objective = ""
        instance.assessment = ""
        instance.plan = ""
        
        if user:
            instance.written_by = user.get_full_name()
        
        if commit:
            instance.save()
        return instance

class ReportForm(forms.ModelForm):
    class Meta:
        model = Reports
        fields = [
            'blood_pressure',
            'heart_rate',
            'spo2',
            'temperature',
            'symptoms'
        ]
