from django.conf import settings
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import UserSerializer


def _set_auth_cookie(response, name, token, max_age):
    response.set_cookie(
        name,
        token,
        max_age=max_age,
        httponly=settings.AUTH_COOKIE_HTTP_ONLY,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        path=settings.AUTH_COOKIE_PATH,
    )


def _apply_tokens(response, access=None, refresh=None):
    if access is not None:
        _set_auth_cookie(
            response, settings.AUTH_COOKIE, access,
            int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()),
        )
    if refresh is not None:
        _set_auth_cookie(
            response, settings.AUTH_REFRESH_COOKIE, refresh,
            int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()),
        )


@method_decorator(ensure_csrf_cookie, name='dispatch')
class CookieTokenObtainPairView(TokenObtainPairView):
    """Validate credentials and deliver the tokens as httpOnly cookies (not JSON)."""
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as exc:
            raise InvalidToken(exc.args[0])

        data = serializer.validated_data
        response = Response({'detail': 'Login successful.'}, status=status.HTTP_200_OK)
        _apply_tokens(response, access=str(data['access']), refresh=str(data['refresh']))
        return response


class CookieTokenRefreshView(TokenRefreshView):
    """Refresh using the refresh cookie; re-set rotated tokens as cookies."""

    def post(self, request, *args, **kwargs):
        refresh = request.COOKIES.get(settings.AUTH_REFRESH_COOKIE)
        if not refresh:
            return Response({'detail': 'No refresh token.'}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = self.get_serializer(data={'refresh': refresh})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as exc:
            raise InvalidToken(exc.args[0])

        data = serializer.validated_data
        response = Response({'detail': 'Token refreshed.'}, status=status.HTTP_200_OK)
        # ROTATE_REFRESH_TOKENS returns a new refresh token too.
        _apply_tokens(response, access=str(data['access']), refresh=data.get('refresh') and str(data['refresh']))
        return response


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = Response({'detail': 'Logged out.'}, status=status.HTTP_200_OK)
        # Best-effort: blacklist the refresh token so it cannot be reused.
        refresh = request.COOKIES.get(settings.AUTH_REFRESH_COOKIE)
        if refresh:
            try:
                RefreshToken(refresh).blacklist()
            except TokenError:
                pass
        response.delete_cookie(settings.AUTH_COOKIE, path=settings.AUTH_COOKIE_PATH)
        response.delete_cookie(settings.AUTH_REFRESH_COOKIE, path=settings.AUTH_COOKIE_PATH)
        return response


@method_decorator(ensure_csrf_cookie, name='dispatch')
class MeView(APIView):
    """Who-am-I check for the SPA (the token cookie is httpOnly and unreadable by JS)."""
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return Response(UserSerializer(request.user).data)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class CSRFView(APIView):
    """Bootstrap endpoint: sets the csrftoken cookie the SPA echoes as X-CSRFToken."""
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        return Response({'detail': 'CSRF cookie set.'})
