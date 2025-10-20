from .models import Referral
from django.views.generic import ListView, CreateView, View
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect

class ReferralListView(ListView):
    model = Referral
    template_name = 'referral/referral_list.html'
    context_object_name = 'referrals'
    paginate_by = 20

    def get_queryset(self):
        return Referral.get_all_referrals()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_count'] = Referral.objects.count()
        context['pending_count'] = Referral.objects.filter(contacted=False).count()
        context['contacted_count'] = Referral.objects.filter(contacted=True).count()
        context['rewarded_count'] = Referral.objects.filter(referrer_rewarded=True).count()
        return context
    
class ContactedReferralListView(ListView):
    model = Referral
    template_name = 'referral/referral_list.html'
    context_object_name = 'referrals'
    paginate_by = 20

    def get_queryset(self):
        return Referral.get_contacted_referrals()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_count'] = Referral.objects.count()
        context['pending_count'] = Referral.objects.filter(contacted=False).count()
        context['contacted_count'] = Referral.objects.filter(contacted=True).count()
        context['rewarded_count'] = Referral.objects.filter(referrer_rewarded=True).count()
        return context
    
class UncontactedReferralListView(ListView):
    model = Referral
    template_name = 'referral/referral_list.html'
    context_object_name = 'referrals'
    paginate_by = 20

    def get_queryset(self):
        return Referral.get_uncontacted_referrals()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_count'] = Referral.objects.count()
        context['pending_count'] = Referral.objects.filter(contacted=False).count()
        context['contacted_count'] = Referral.objects.filter(contacted=True).count()
        context['rewarded_count'] = Referral.objects.filter(referrer_rewarded=True).count()
        return context
    
class RewardedReferralListView(ListView):
    model = Referral
    template_name = 'referral/referral_list.html'
    context_object_name = 'referrals'
    paginate_by = 20

    def get_queryset(self):
        return Referral.get_rewarded_referrals()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_count'] = Referral.objects.count()
        context['pending_count'] = Referral.objects.filter(contacted=False).count()
        context['contacted_count'] = Referral.objects.filter(contacted=True).count()
        context['rewarded_count'] = Referral.objects.filter(referrer_rewarded=True).count()
        return context
    
class UnrewardedReferralListView(ListView):
    model = Referral
    template_name = 'referral/referral_list.html'
    context_object_name = 'referrals'
    paginate_by = 20

    def get_queryset(self):
        return Referral.get_unrewarded_referrals()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_count'] = Referral.objects.count()
        context['pending_count'] = Referral.objects.filter(contacted=False).count()
        context['contacted_count'] = Referral.objects.filter(contacted=True).count()
        context['rewarded_count'] = Referral.objects.filter(referrer_rewarded=True).count()
        return context


class ReferralCreateView(CreateView):
    model = Referral
    fields = ['patient_name', 'patient_email', 'patient_phone', 'referred_by', 'referred_by_email']
    template_name = 'referral/referral_form.html'
    success_url = '/'

    def form_valid(self, form):
        message = "Thank you for your referral! We will contact the referred patient soon."
        messages.success(self.request, message)
        return super().form_valid(form)
    

class ReferralAPIView(View):
    def post(self, request):
        try:
            # Get data from form submission
            referrer_name = request.POST.get('referrer_name')
            referrer_email = request.POST.get('referrer_email')
            patient_name = request.POST.get('patient_name')
            patient_phone = request.POST.get('patient_phone')
            patient_email = request.POST.get('patient_email', '')
            
            # Validate required fields
            if not all([referrer_name, referrer_email, patient_name, patient_phone]):
                return JsonResponse({
                    'success': False,
                    'message': 'Please fill in all required fields'
                }, status=400)
            
            # Create referral record - using your model's field names
            referral = Referral.objects.create(
                referred_by=referrer_name,
                referred_by_email=referrer_email,
                patient_name=patient_name,
                patient_phone=patient_phone,
                patient_email=patient_email
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Thank you for your referral! We will contact them within 24 hours.',
                'referral_id': referral.id
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error submitting referral: {str(e)}'
            }, status=400)
        

# Admin Actions
class MarkAsContactedView(View):
    def get(self, request, pk):
        return self.post(request, pk)
    
    def post(self, request, pk):
        try:
            referral = Referral.objects.get(pk=pk)
            referral.mark_as_contacted()
            messages.success(request, f"Referral for {referral.patient_name} marked as contacted.")
        except Referral.DoesNotExist:
            messages.error(request, "Referral not found.")
        except Exception as e:
            messages.error(request, f"Error updating referral: {str(e)}")
        
        return redirect('referral:list')
    
class MarkAsRewardedView(View):
    def get(self, request, pk):
        return self.post(request, pk)
    
    def post(self, request, pk):
        try:
            referral = Referral.objects.get(pk=pk)
            referral.mark_as_rewarded()
            messages.success(request, f"Referral reward for {referral.patient_name} marked as processed.")
        except Referral.DoesNotExist:
            messages.error(request, "Referral not found.")
        except Exception as e:
            messages.error(request, f"Error updating referral: {str(e)}")
        
        return redirect('referral:list')