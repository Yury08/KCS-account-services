import secrets
import string
import uuid
from typing import NoReturn, Optional, Union

import jwt
import redis
from asgiref.sync import sync_to_async
from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import exceptions, status
from rest_framework.exceptions import NotFound

redis_obj = redis.StrictRedis(host=settings.REDIS_HOST,
                              port=settings.REDIS_PORT,
                              db=settings.REDIS_DB,
                              decode_responses=True)


def generate_password(length: int) -> str:
    """Функция генерирует уникальный и надежный пароль"""
    characters: list = string.ascii_letters + string.digits
    password: str = ''.join(secrets.choice(characters) for _ in range(length))
    return password


@sync_to_async
def get_user(username: str) -> Union[User | NoReturn]:
    """Вытягиваем текущего пользователя из бд"""
    try:
        return User.objects.get(username=username)
    except Exception:
        raise NotFound(detail=f"Не удалось получить пользователя с {username} из базы данных",
                       code=status.HTTP_404_NOT_FOUND)


def create_message(email: str, token: uuid, username: str) -> str:
    """Функция создает каркас сообщения для отправки пользователю"""
    try:
        link = reverse('signin', kwargs={'email': email, 'token': token})
        password: str = generate_password(12)
        redis_obj.set(f'{username}', password)
        verification_link: str = f'{settings.DOMAIN_NAME}{link}'
        message: str = f'Благодарим вас за регистрацию в KravzovCRM. Ваши данные для входа в систему: ' \
                       f'{username} - логин, ' \
                       f'{token} - уникальный id вашего аккаунта, ' \
                       f'{password} - пароль. ' \
                       f'Для входа перейдите по ссылке: <a href="{verification_link}">{verification_link}</a>'
        return message
    except Exception as e:
        return f"В ходе выполнения функции create_message произошла ошибка {e}"


def get_payload(request) -> dict:
    """Функция для получения аккаунта пользователя через refresh token"""
    refresh_token: Optional[str] = request.COOKIES.get('refreshtoken')
    if refresh_token is None:
        raise exceptions.AuthenticationFailed('Authentication credentials were not provided.')
    try:
        payload = jwt.decode(
            refresh_token, settings.REFRESH_TOKEN_SECRET, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        # здесь можно вставить middleware, который мне отправлял Игорь Владимирович
        raise exceptions.AuthenticationFailed('expired refresh token, please login again.')
    return payload
