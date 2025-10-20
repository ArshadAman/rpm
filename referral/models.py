from django.db import models

# Create your models here.
class Referral(models.Model):
    patient_name = models.CharField(max_length=100)
    patient_email = models.EmailField(max_length=100)
    patient_phone = models.CharField(max_length=15)
    referred_by = models.CharField(max_length=100)
    referred_by_email = models.EmailField(max_length=100)
    contacted = models.BooleanField(default=False)
    referrer_rewarded = models.BooleanField(default=False)
    referral_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Referral of {self.patient_name} by {self.referred_by} on {self.referral_date}"
    
    def get_all_referrals():
        return Referral.objects.all().order_by('-referral_date')
    
    def get_contacted_referrals():
        return Referral.objects.filter(contacted=True).order_by('-referral_date')
    
    def get_uncontacted_referrals():
        return Referral.objects.filter(contacted = False).order_by('-referral_date')
    
    def get_rewarded_referrals():
        return Referral.objects.filter(referrer_rewarded=True).order_by('-referral_date')
    
    def get_unrewarded_referrals():
        return Referral.objects.filter(referrer_rewarded=False).order_by('-referral_date')
    
    def mark_as_contacted(self):
        self.contacted = True
        self.save()
    
    def mark_as_rewarded(self):
        self.referrer_rewarded = True
        self.save()
