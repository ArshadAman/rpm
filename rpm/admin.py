from django.contrib.admin import AdminSite
from django.contrib.auth.models import User, Group
from rpm_users.models import Patient, Moderator, PastMedicalHistory
from reports.models import Reports, Documentation

class CustomAdminSite(AdminSite):
    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['total_users'] = User.objects.count()
        extra_context['total_patients'] = Patient.objects.count()
        extra_context['active_moderators'] = Moderator.objects.filter(user__is_active=True).count()
        extra_context['total_reports'] = Reports.objects.count()
        return super().index(request, extra_context)

admin_site = CustomAdminSite()

# Register models with custom admin site
admin_site.register(User)
admin_site.register(Group)
admin_site.register(Patient)
admin_site.register(Moderator)
admin_site.register(PastMedicalHistory)
admin_site.register(Reports)
admin_site.register(Documentation) 