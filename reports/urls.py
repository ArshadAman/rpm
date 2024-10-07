from django.urls import path
from . import views
urlpatterns = [
    path('create-report/', view=views.create_report),
    path('get-your-report/', view=views.get_your_reports),
    path('get-patient-report/', view=views.get_patients_reports),
    path('get-single-report/<uuid:report_id>/', view=views.get_single_report)
]
