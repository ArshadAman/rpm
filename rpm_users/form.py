from django import forms
from reports.models import Documentation

class DocumentationForm(forms.ModelForm):
    class Meta:
        model = Documentation
        fields = ['title', 'history_of_present_illness', 'chief_complaint', 'subjective', 'objective', 'assessment', 'plan', 'file']