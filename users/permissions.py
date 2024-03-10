from typing import Dict, Optional

import jwt
import redis
from django.conf import settings
from rest_framework import exceptions
from rest_framework.permissions import BasePermission

from .models import Account, BlackListedToken

redis_obj = redis.StrictRedis(host=settings.REDIS_HOST,
                              port=settings.REDIS_PORT,
                              db=settings.REDIS_DB,
                              decode_responses=True)


class IsAdminAccount(BasePermission):
    def has_permission(self, request, view):
        try:
            authorization_header: Optional[str] = request.headers.get('Authorization')
            access_token: Optional[str] = authorization_header.split()[1]
            payload: Dict[str] = jwt.decode(access_token, settings.SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('access_token expired')
        except IndexError:
            raise exceptions.AuthenticationFailed('Token prefix missing')

        account = Account.objects.get(id=payload['account_id'])
        if account.is_admin:
            return True
        return False


class IsTokenValid(BasePermission):
    def has_permission(self, request, view):
        user_id = request.user.id
        is_allowed_user = True
        token = request.COOKIES.get('refreshtoken')
        try:
            is_blackListed = BlackListedToken.objects.get(user=user_id, token=token)
            if is_blackListed:
                is_allowed_user = False
        except BlackListedToken.DoesNotExist:
            is_allowed_user = True
        return is_allowed_user
