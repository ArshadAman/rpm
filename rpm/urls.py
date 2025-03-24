from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('rpm_users.urls')),
    path('reports/', include('reports.urls')),
    
    path('grappelli/', include('grappelli.urls')),  # Grappelli URLS
]
