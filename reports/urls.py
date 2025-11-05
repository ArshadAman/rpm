from django.urls import path
from . import views

# app_name = 'reports'

urlpatterns = [
    path('create-report/', view=views.create_report),
    path('get-your-report/', view=views.get_your_reports),
    path('get-all-reports/<uuid:patient_id>/', view=views.get_all_reports, name='get_all_reports'),
    path('get-patient-report/', view=views.get_patients_reports),
    path('get-single-report/<int:report_id>/', view=views.get_single_report, name='get_single_report'),
    path('get-single-report/<str:report_id>/', view=views.get_single_report, name='get_single_report'),
    path('<uuid:patient_id>/add-documentation/', views.add_documentation, name='add_documentation'),
    path('edit-documentation/<int:doc_id>/', views.edit_documentation, name='edit_documentation'),
    path('data-telemetry/', views.data_from_mio_connect, name='data_telemetry'),
    path('edit-patient/<uuid:patient_id>/', views.edit_patient, name='edit_patient'),
    path('documentation/<int:doc_id>/view/', views.documentation_share_view, name='documentation_share_view'),
    
    # New report management endpoints
    path('update-report/<int:report_id>/', views.update_report, name='update_report'),
    path('create-report-manual/', views.create_report_manual, name='create_report_manual'),
    path('get-recent-reports/<uuid:patient_id>/', views.get_recent_reports, name='get_recent_reports'),
    
    # Export vitals endpoint
    path('export-vitals/<uuid:patient_id>/', views.export_vitals_excel, name='export_vitals_excel'),
]
