from django.urls import path
from . import views

app_name = 'referral'

urlpatterns = [
    # List views for different referral types
    path('', views.ReferralListView.as_view(), name='list'),
    path('contacted/', views.ContactedReferralListView.as_view(), name='contacted'),
    path('uncontacted/', views.UncontactedReferralListView.as_view(), name='uncontacted'),
    path('rewarded/', views.RewardedReferralListView.as_view(), name='rewarded'),
    path('unrewarded/', views.UnrewardedReferralListView.as_view(), name='unrewarded'),
    
    # Create referral form
    path('create/', views.ReferralCreateView.as_view(), name='create'),
    
    # API endpoint for AJAX form submission (from your landing page)
    path('api/submit/', views.ReferralAPIView.as_view(), name='api_submit'),
    
    # Admin actions
    path('<int:pk>/mark-contacted/', views.MarkAsContactedView.as_view(), name='mark_contacted'),
    path('<int:pk>/mark-rewarded/', views.MarkAsRewardedView.as_view(), name='mark_rewarded'),
]

