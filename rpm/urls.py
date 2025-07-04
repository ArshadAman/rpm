from django.urls import path, include
from rpm_users.views import admin_logout
from .admin import admin_site
from reports.views import documentation_share_view

urlpatterns = [
    path('admin/logout/', admin_logout, name='admin_logout'),  # Must come before admin.site.urls
    path('admin/', admin_site.urls),
    path('', include('rpm_users.urls')),
    path('reports/', include('reports.urls')),
    path('documentation/<int:doc_id>/view/', documentation_share_view, name='documentation_share_view_global'),

    path('grappelli/', include('grappelli.urls')),  # Grappelli URLS
]
