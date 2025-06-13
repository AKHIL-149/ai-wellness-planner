# backend/wellness_planner/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Authentication
    path('api/auth/login/', obtain_auth_token, name='api_token_auth'),
    
    # API endpoints
    path('api/users/', include('apps.users.urls')),
    path('api/nutrition/', include('apps.nutrition.urls')),
    path('api/fitness/', include('apps.fitness.urls')),
    path('api/chat/', include('apps.chat.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)