from django.urls import path
from . import views

app_name = 'medications'

urlpatterns = [
    # Medicine Search URLs
    path('search-medicines/', views.search_medicines_by_disease, name='search_medicines_by_disease'),
    path('check-interactions/', views.check_drug_interactions, name='check_drug_interactions'),
    
    # Cache Management URLs
    path('cached-medicines/', views.get_cached_medicines, name='get_cached_medicines'),
    path('refresh-cache/', views.refresh_medicine_cache, name='refresh_medicine_cache'),
    
    # API endpoints for frontend
    path('api/diseases/', views.get_diseases_list, name='get_diseases_list'),
    path('api/medicines/<int:medicine_id>/', views.get_medicine_detail, name='get_medicine_detail'),
    path('api/popular-searches/', views.get_popular_searches, name='get_popular_searches'),
    
    # Patient Medicine History
    path('patient/<int:patient_id>/medicine-history/', views.get_patient_medicine_history, name='patient_medicine_history'),
    path('log-medicine-view/', views.log_medicine_view, name='log_medicine_view'),
    
    # Analytics (Optional)
    path('analytics/search-stats/', views.get_search_analytics, name='search_analytics'),
    path('analytics/cache-stats/', views.get_cache_analytics, name='cache_analytics'),
]