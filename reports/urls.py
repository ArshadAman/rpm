from django.urls import path
from . import views
urlpatterns = [
    path('create-report/', view=views.create_report),
    path('get-your-report/', view=views.get_your_reports),
    path('get-patient-report/', view=views.get_patients_reports),
    path('get-single-report/<int:report_id>/', view=views.get_single_report, name='get_single_report'),
    path('reports/<int:report_id>/add-documentation/', views.add_documentation, name='add_documentation'),
]
