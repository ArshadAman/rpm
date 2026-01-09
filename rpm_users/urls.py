from django.urls import path
from . import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('add-patient/', views.create_patient),
    path('patient-token-refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', views.landing_page, name='landing'),
    path('home/', views.home, name='home'),
    path('home', views.home),
    path('moderator_login/', views.moderator_login, name='moderator_login'),
    path('patient_register/', views.patient_self_registration, name='patient_register'),
    path('send-email-otp/', views.send_email_otp, name='send_email_otp'),
    path('verify-email-otp/', views.verify_email_otp, name='verify_email_otp'),
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
    
    # Admin dashboard
    path('admin-access/', views.admin_access, name='admin_access'),
    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-logout/', views.admin_logout, name='admin_logout'),
    
    # Moderator management
    path('dashboard/moderators/', views.moderator_list, name='moderator_list'),
    path('dashboard/moderators/create/', views.moderator_create, name='moderator_create'),
    path('dashboard/moderators/<int:moderator_id>/', views.moderator_detail, name='moderator_detail'),
    path('dashboard/moderators/<int:moderator_id>/edit/', views.moderator_edit, name='moderator_edit'),
    path('dashboard/moderators/<int:moderator_id>/delete/', views.moderator_delete, name='moderator_delete'),
    
    # Doctor management
    path('dashboard/doctors/', views.doctor_list, name='doctor_list'),
    path('dashboard/doctors/create/', views.doctor_create, name='doctor_create'),
    path('dashboard/doctors/<int:doctor_id>/', views.doctor_detail, name='doctor_detail'),
    path('dashboard/doctors/<int:doctor_id>/edit/', views.doctor_edit, name='doctor_edit'),
    path('dashboard/doctors/<int:doctor_id>/delete/', views.doctor_delete, name='doctor_delete'),
    
    # Patient information management
    path('dashboard/patients/', views.admin_patient_list, name='admin_patient_list'),
    path('dashboard/patients/<uuid:patient_id>/', views.admin_patient_detail, name='admin_patient_detail'),
    
    # Leads management
    path('dashboard/leads/', views.leads_list, name='leads_list'),
    path('dashboard/leads/delete-all/', views.delete_all_leads, name='delete_all_leads'),
    path('dashboard/leads/<int:lead_id>/', views.lead_detail, name='lead_detail'),
    path('dashboard/leads/<int:lead_id>/delete/', views.delete_lead, name='delete_lead'),
    path('dashboard/leads/<int:lead_id>/convert/', views.convert_lead_to_patient, name='convert_lead_to_patient'),
    path('dashboard/leads-call-summaries/', views.leads_call_summaries_list, name='leads_call_summaries'),
    
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
    
    # Video management
    path('dashboard/videos/', views.video_list, name='video_list'),
    path('dashboard/videos/create/', views.video_create, name='video_create'),
    path('dashboard/videos/<uuid:video_id>/edit/', views.video_edit, name='video_edit'),
    path('dashboard/videos/<uuid:video_id>/delete/', views.video_delete, name='video_delete'),
    path('dashboard/videos/<uuid:video_id>/toggle-active/', views.video_toggle_active, name='video_toggle_active'),
    path('dashboard/videos/reorder/', views.video_reorder, name='video_reorder'),
    
    # Public API for videos
    path('api/videos/active/', views.get_active_videos, name='get_active_videos'),
    
    # Testimonial management
    path('dashboard/testimonials/', views.testimonial_list, name='testimonial_list'),
    path('dashboard/testimonials/create/', views.testimonial_create, name='testimonial_create'),
    path('dashboard/testimonials/<uuid:testimonial_id>/edit/', views.testimonial_edit, name='testimonial_edit'),
    path('dashboard/testimonials/<uuid:testimonial_id>/delete/', views.testimonial_delete, name='testimonial_delete'),
    path('dashboard/testimonials/<uuid:testimonial_id>/toggle-active/', views.testimonial_toggle_active, name='testimonial_toggle_active'),
    path('dashboard/testimonials/reorder/', views.testimonial_reorder, name='testimonial_reorder'),
    
    # Public API for testimonials
    path('api/testimonials/active/', views.get_active_testimonials, name='get_active_testimonials'),
    
    # Patient status and sticky notes API
    path('api/patient/<uuid:patient_id>/status/', views.update_patient_status, name='update_patient_status'),
    path('api/patient/<uuid:patient_id>/sticky-note/', views.update_patient_sticky_note, name='update_patient_sticky_note'),
    path('api/patient/<uuid:patient_id>/get-sticky-note/', views.get_patient_sticky_note, name='get_patient_sticky_note'),
    path('lab-portal/', views.lab_upload, name='lab_upload'),
    
    # Lab Portal APIs
    path('api/labs/structure/', views.get_lab_structure, name='get_lab_structure'),
    path('api/labs/patient/<str:patient_id>/', views.get_patient_labs, name='get_patient_labs'),
    path('api/labs/save/', views.save_lab_result, name='save_lab_result'),
]
