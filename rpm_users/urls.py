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
    path('', views.home),
    path('moderator_login/', views.moderator_login, name='moderator_login'),
    path('patient_register/', views.patient_self_registration, name='patient_register'),
    path('registration-success/', views.registration_success, name='registration_success'),
    path('update-patient/', views.update_patient),
    path('view-patient/<str:patient_id>/', views.moderator_actions_view, name='moderator_actions'),
    path('view-patient/', views.view_assigned_patient, name='view_all_assigned_patient'),
    path('logout/', views.moderator_logout, name='moderator_logout'),
    path('register-patient/', views.register_patient, name='register_patient'),
    path('write_document/<int:report_id>/', views.write_document, name='write_document'),
    path('view_all_assigned_patient/', views.view_assigned_patient, name='view_all_assigned_patient'),
    path('view_documentation/<uuid:patient_id>/', views.view_documentation, name='view_documentation'),
]
