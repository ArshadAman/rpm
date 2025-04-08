from django import forms
from .models import Documentation

class DocumentationForm(forms.ModelForm):
    class Meta:
        model = Documentation
        fields = [
            "title",
            "history_of_present_illness",
            "chief_complaint",
            "subjective",
            "objective",
            "assessment",
            "plan",
            "file",
        ]
        widgets = {
            "history_of_present_illness": forms.Textarea(attrs={"rows": 3}),
            "chief_complaint": forms.Textarea(attrs={"rows": 2}),
            "subjective": forms.Textarea(attrs={"rows": 2}),
            "objective": forms.Textarea(attrs={"rows": 2}),
            "assessment": forms.Textarea(attrs={"rows": 2}),
            "plan": forms.Textarea(attrs={"rows": 2}),
        }
