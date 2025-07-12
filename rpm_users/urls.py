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
    # path('edit-documentation/<int:doc_id>/', views.edit_documentation, name='edit_documentation'),
    path('doctor_login/', views.doctor_login, name='doctor_login'),
    # path('doctor_dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('doctor_logout/', views.doctor_logout, name='doctor_logout'),
    path('doctor/patient/<uuid:patient_id>/', views.doctor_patient_detail, name='doctor_patient_detail'),
    path('view_escalated_patient/', views.view_escalated_patient, name='view_escalated_patient'),
    path('escalate_patient/<uuid:patient_id>/', views.escalate_patient, name='escalate_patient'),
    
    # Admin-verified user creation
    path('staff/create-user/', views.admin_create_user, name='admin_create_user'),
    path('staff/verify-password/', views.verify_admin_password, name='verify_admin_password'),
    path('staff/create-account/', views.create_staff_user, name='create_staff_user'),
    path('test-staff-ui/', views.test_staff_ui, name='test_staff_ui'),
    
    # Shortcut management API endpoints
    path('api/shortcuts/', views.get_shortcuts, name='get_shortcuts'),
    path('api/shortcuts/create/', views.create_shortcut, name='create_shortcut'),
    path('api/shortcuts/<int:shortcut_id>/update/', views.update_shortcut, name='update_shortcut'),
    path('api/shortcuts/<int:shortcut_id>/delete/', views.delete_shortcut, name='delete_shortcut'),
    path('api/shortcuts/search/', views.search_shortcuts, name='search_shortcuts'),
]
