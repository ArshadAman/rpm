from django.urls import path
from . import views
urlpatterns = [
    path('add-patient/', views.create_patient),
    path('', views.moderator_login),
    path('update-patient/', views.update_patient),
    path('view-patient/<str:patient_id>/', views.moderator_actions_view, name='moderator_actions'),
    path('view-patient/', views.view_assigned_patient, name='view_all_assigned_patient'),
    path('logout/', views.moderator_logout, name='moderator_logout')
]
