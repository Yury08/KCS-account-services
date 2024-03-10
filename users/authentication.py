from typing import Dict, Optional

import jwt
from django.conf import settings
from django.contrib.auth.models import User
from django.middleware.csrf import CsrfViewMiddleware
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication


class CSRFCheck(CsrfViewMiddleware):
    def _reject(self, request, reason):
        """
        Вернуть причину неудачи вместо Httpresponse
        """
        return reason


def dummy_get_response(request):  # pragma: no cover
    """Просто костыль"""
    return None


def enforce_csrf(request) -> Optional[exceptions.PermissionDenied]:
    """
    Принудительная проверка CSRF
    """
    check = CSRFCheck(dummy_get_response)
    check.process_request(request)
    reason = check.process_view(request, None, (), {})
    print(reason)
    if reason:
        return exceptions.PermissionDenied(f'CSRF Failed: {reason}')


class SafeJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        """
        Переопределение метода authenticate на аутентификацию по JWT токенам
        """
        authorization_header: Optional[str] = request.headers.get('Authorization')

        if not authorization_header:
            return None
        try:
            access_token: Optional[str] = authorization_header.split()[1]
            payload: Dict[str] = jwt.decode(access_token, settings.SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('access_token expired')
        except IndexError:
            raise exceptions.AuthenticationFailed('Token prefix missing')

        user: User = User.objects.get(id=payload['user_id'])
        if user is None:
            raise exceptions.AuthenticationFailed('User not found')

        enforce_csrf(request)
        return user, None
