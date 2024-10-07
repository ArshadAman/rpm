from django.contrib import admin
from django.utils.html import format_html
from .models import Moderator, Patient
from reports.models import Reports

class ReportInline(admin.TabularInline):
    model = Reports
    extra = 0  # No extra empty forms

class PatientAdmin(admin.ModelAdmin):
    inlines = [ReportInline]  # Show related reports in the patient admin
    list_display = ('email', 'first_name', 'last_name', 'date_of_birth', 'height', 'weight', 'get_reports')
    
    def get_reports(self, obj):
        reports = Reports.objects.filter(patient=obj)
        report_details = []
        for report in reports:
            report_details.append(f"{report.created_at} - {report.patient.last_name}")
        return format_html("<br>".join(report_details))

    get_reports.short_description = 'Reports'

# Register with the customized admin class
admin.site.register(Patient, PatientAdmin)
admin.site.register(Moderator)
