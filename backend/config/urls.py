"""URL configuration for config project."""
from django.contrib import admin
from django.urls import path, include

from api.auth_views import (
    AcceptInvitationView,
    CookieTokenObtainPairView,
    CookieTokenRefreshView,
    InvitationDetailView,
    LogoutView,
    MeView,
    CSRFView,
)
from api.cron_views import SendRemindersView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),

    # Cookie-based auth (httpOnly access/refresh + CSRF)
    path('api/auth/login/', CookieTokenObtainPairView.as_view(), name='auth_login'),
    path('api/auth/refresh/', CookieTokenRefreshView.as_view(), name='auth_refresh'),
    path('api/auth/logout/', LogoutView.as_view(), name='auth_logout'),
    path('api/auth/me/', MeView.as_view(), name='auth_me'),
    path('api/auth/csrf/', CSRFView.as_view(), name='auth_csrf'),

    # Public invitation acceptance (Chancellors send invites via /api/invitations/)
    path('api/auth/invitation/', InvitationDetailView.as_view(), name='auth_invitation_detail'),
    path('api/auth/accept-invite/', AcceptInvitationView.as_view(), name='auth_accept_invite'),

    # Triggered by Vercel Cron (bearer CRON_SECRET)
    path('api/cron/send-reminders/', SendRemindersView.as_view(), name='cron_send_reminders'),
]
