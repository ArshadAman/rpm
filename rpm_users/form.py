from django import forms
from reports.models import Documentation

class DocumentationForm(forms.ModelForm):
    class Meta:
        model = Documentation
        fields = ['title', 'description', 'chief_complaint', 'subjective', 'objective', 'assessment', 'plan', 'file']