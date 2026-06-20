from django.conf import settings
from rest_framework import exceptions
from rest_framework.authentication import CSRFCheck
from rest_framework_simplejwt.authentication import JWTAuthentication


def _enforce_csrf(request):
    """Run Django's CSRF check the same way DRF's SessionAuthentication does."""
    def dummy_get_response(_request):
        return None

    check = CSRFCheck(dummy_get_response)
    check.process_request(request)
    reason = check.process_view(request, None, (), {})
    if reason:
        raise exceptions.PermissionDenied(f'CSRF Failed: {reason}')


class CookieJWTAuthentication(JWTAuthentication):
    """
    Authenticates from the httpOnly access-token cookie set at login.

    Because the credential now travels automatically with every request (a
    cookie), we must defend against CSRF — enforced here for unsafe methods,
    exactly as Django's session auth does. Requests without the cookie return
    None so header-based JWT auth can still serve non-browser clients.
    """

    def authenticate(self, request):
        raw_token = request.COOKIES.get(settings.AUTH_COOKIE)
        if not raw_token:
            return None

        validated_token = self.get_validated_token(raw_token)
        user = self.get_user(validated_token)
        _enforce_csrf(request)
        return (user, validated_token)
