from django.contrib import admin
from .models import Referral
from rpm.admin import admin_site

# Create a custom admin class for better display
class ReferralAdmin(admin.ModelAdmin):
    list_display = ['patient_name', 'referred_by', 'referral_date', 'contacted', 'referrer_rewarded']
    list_filter = ['contacted', 'referrer_rewarded', 'referral_date']
    search_fields = ['patient_name', 'referred_by', 'patient_email', 'referred_by_email']
    readonly_fields = ['referral_date']
    list_editable = ['contacted', 'referrer_rewarded']
    date_hierarchy = 'referral_date'
    
    fieldsets = (
        ('Patient Information', {
            'fields': ('patient_name', 'patient_email', 'patient_phone')
        }),
        ('Referrer Information', {
            'fields': ('referred_by', 'referred_by_email')
        }),
        ('Status', {
            'fields': ('contacted', 'referrer_rewarded', 'referral_date')
        }),
    )

# Register with the custom admin site
admin_site.register(Referral, ReferralAdmin)