from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from config.admin import veloma_admin_site
from config.authentication.admin_recovery import admin_recovery_urlpatterns
from config.common.views import health

urlpatterns = [
    # Admin password recovery is mounted before the admin site so its named URLs
    # (used in templates and emails) resolve under /admin/.
    path('admin/', include(admin_recovery_urlpatterns)),
    path('admin/', veloma_admin_site.urls),
    path('health/', health, name='health'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/auth/', include('config.authentication.urls')),
    path('api/client-portal/', include('app.client_portal.urls')),
]
