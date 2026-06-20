"""URL configuration for config project."""
from django.contrib import admin
from django.urls import path, include

from api.auth_views import (
    CookieTokenObtainPairView,
    CookieTokenRefreshView,
    LogoutView,
    MeView,
    CSRFView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),

    # Cookie-based auth (httpOnly access/refresh + CSRF)
    path('api/auth/login/', CookieTokenObtainPairView.as_view(), name='auth_login'),
    path('api/auth/refresh/', CookieTokenRefreshView.as_view(), name='auth_refresh'),
    path('api/auth/logout/', LogoutView.as_view(), name='auth_logout'),
    path('api/auth/me/', MeView.as_view(), name='auth_me'),
    path('api/auth/csrf/', CSRFView.as_view(), name='auth_csrf'),
]
