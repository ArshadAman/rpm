from django.contrib import admin
from django.utils.html import format_html
from .models import Moderator, Patient, PastMedicalHistory, Interest, InterestPastMedicalHistory, InterestLead
from reports.models import Reports

# class ReportInline(admin.TabularInline):
#     model = Reports
#     extra = 0  # No extra empty forms

# class PatientAdmin(admin.ModelAdmin):
#     inlines = [ReportInline]  # Show related reports in the patient admin
#     list_display = ('email', 'first_name', 'last_name', 'date_of_birth', 'height', 'weight', 'get_reports')
    
#     def get_reports(self, obj):
#         reports = Reports.objects.filter(patient=obj)
#         report_details = []
#         for report in reports:
#             report_details.append(f"{report.created_at} - {report.patient.last_name}")
#         return format_html("<br>".join(report_details))

#     get_reports.short_description = 'Reports'

# Register the Patient model
admin.site.register(Patient)

# Register the Moderator model
admin.site.register(Moderator)

# Register the PastMedicalHistory model
admin.site.register(PastMedicalHistory)

# Create inline admin class for InterestPastMedicalHistory
class InterestPastMedicalHistoryInline(admin.TabularInline):
    model = InterestPastMedicalHistory
    extra = 0

# Create admin class for Interest model
class InterestAdmin(admin.ModelAdmin):
    inlines = [InterestPastMedicalHistoryInline]
    list_display = ('first_name', 'last_name', 'email', 'phone_number', 'service_interest', 'created_at')
    list_filter = ('service_interest', 'created_at', 'good_eyesight', 'can_follow_instructions', 'can_take_readings')
    search_fields = ('first_name', 'last_name', 'email', 'insurance')
    readonly_fields = ('created_at',)

# Register the Interest model with custom admin class
admin.site.register(Interest, InterestAdmin)

# Register the InterestPastMedicalHistory model separately
admin.site.register(InterestPastMedicalHistory)

# Register the InterestLead model
@admin.register(InterestLead)
class InterestLeadAdmin(admin.ModelAdmin):
    list_display = [field.name for field in InterestLead._meta.fields]
    search_fields = ['email', 'first_name', 'last_name', 'phone_number']

# Debug section to print registered models
print("==== DEBUG: REGISTERED MODELS IN ADMIN ====")
from django.contrib import admin
print(admin.site._registry.keys())
print("==========================================")
