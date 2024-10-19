from django.urls import path
from . import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
urlpatterns = [
    path('add-patient/', views.create_patient),
    path('patient-login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('patient-token-refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', views.moderator_login),
    path('update-patient/', views.update_patient),
    path('view-patient/<str:patient_id>/', views.moderator_actions_view, name='moderator_actions'),
    path('view-patient/', views.view_assigned_patient, name='view_all_assigned_patient'),
    path('logout/', views.moderator_logout, name='moderator_logout')
]
