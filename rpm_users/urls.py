from django.urls import path
from . import views
urlpatterns = [
    path('add-patient/', views.create_patient),
    path('add-moderator/', views.create_moderator),
    path('update-patient/', views.update_patient),
]
