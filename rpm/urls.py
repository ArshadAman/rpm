from django.urls import path, include
from rpm_users.views import admin_logout
from .admin import admin_site

urlpatterns = [
    path('admin/logout/', admin_logout, name='admin_logout'),  # Must come before admin.site.urls
    path('admin/', admin_site.urls),
    path('', include('rpm_users.urls')),
    path('reports/', include('reports.urls')),
    
    path('grappelli/', include('grappelli.urls')),  # Grappelli URLS
    # path('voice_bot/', include('voice_bot.urls')),
]
