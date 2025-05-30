from django.urls import path
from . import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('add-patient/', views.create_patient),
    path('patient-token-refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', views.home, name='home'),
    path('moderator_login/', views.moderator_login, name='moderator_login'),
    path('patient_register/', views.patient_self_registration, name='patient_register'),
    path('patient_login/', views.patient_login, name='patient_login'),
    path('patient_home/', views.patient_home, name='patient_home'),
    path('patient_logout/', views.patient_logout, name='patient_logout'),
    path('registration-success/', views.registration_success, name='registration_success'),
    path('update-patient/', views.update_patient),
    path('view-patient/<str:patient_id>/', views.moderator_actions_view, name='moderator_actions'),
    path('view-patient/', views.view_assigned_patient, name='view_all_assigned_patient'),
    path('logout/', views.moderator_logout, name='moderator_logout'),
    path('register-patient/', views.register_patient, name='register_patient'),
    path('write_document/<int:report_id>/', views.write_document, name='write_document'),
    path('view_all_assigned_patient/', views.view_assigned_patient, name='view_all_assigned_patient'),
    path('view_documentation/<uuid:patient_id>/', views.view_documentation, name='view_documentation'),
    path('express-interest/', views.express_interest, name='express_interest'),
    path('api/track-interest/', views.track_interest, name='track_interest'),
    path('terms-and-conditions/', views.terms_and_conditions_view, name='terms_and_conditions'),
    path('edit-documentation/<int:doc_id>/', views.edit_documentation, name='edit_documentation'),
]
