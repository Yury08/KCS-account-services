import asyncio
import uuid
from typing import Dict, Optional

import redis
from adrf.decorators import api_view as async_api_view
from asgiref.sync import sync_to_async
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework import exceptions, generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Account, BlackListedToken, Company, Profile, ProfileMail
from .permissions import IsAdminAccount, IsTokenValid
from .serializers import (AccountSerializer, CompanySerializer,
                          ProfileMailSerializer, ProfileSerializer,
                          UserSerializer)
from .services import create_message, get_payload, get_user
from .tasks import MailCenter, MessageMail
from .utils import generate_access_token, generate_refresh_token

redis_obj = redis.StrictRedis(host=settings.REDIS_HOST,
                              port=settings.REDIS_PORT,
                              db=settings.REDIS_DB,
                              decode_responses=True)


# API для admin пользователей
class ProfileMailList(generics.ListAPIView):
    """Для просмотра всех конфигураций SMTP"""
    serializer_class = ProfileMailSerializer
    permission_classes = [IsAdminAccount]
    queryset = ProfileMail.objects.all()


# API клиента
@async_api_view(['POST'])
async def registration(request) -> Response:
    """
    Функция для регистрации пользователя через почту
    """
    try:
        serialized = AccountSerializer(data=request.data)
        username: str = serialized.initial_data['username']
        email: str = serialized.initial_data['email']

        if sync_to_async(serialized.is_valid)():
            # если что от сюда убрано поле email при создании пользователя
            await sync_to_async(User.objects.create_user)(username=username, email=email)
            token = uuid.uuid4()
            user: User = await get_user(username=username)

            account: Account = await sync_to_async(Account.objects.create)(user=user, token=token)

            message = create_message(email, token, username)
            await sync_to_async(user.set_password)(redis_obj.get(f"{username}"))
            await sync_to_async(user.save)()
            mess: MessageMail = MessageMail(
                subject="Сообщение для входа на сайт",
                priority=1,
                body=message,
                to=[email])
            mc: MailCenter = MailCenter(None, mess)
            asyncio.ensure_future(mc.send_mail_simple())

            json_account = AccountSerializer(account).data
            json_user = UserSerializer(user).data

            return Response(data={"account": json_account, "user": json_user},
                            status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response(
            data={"detail": f"Что-то пошло не так в ходе регистрации пользователя. {e}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST', 'GET'])
@ensure_csrf_cookie
def signin(request, email: str, token: uuid) -> Response:
    """
        Функция для аутентификации пользователя,
        после его переход по уникальной ссылке, со сгенерированным паролем.
        В функции создается ПРОФИЛЬ пользователя. Она отрабатывает только после регистрации
     """
    if request.method == 'POST':
        try:
            account: Account = Account.objects.get(token=token)
            request.data["account"] = account.id
            serialized = CompanySerializer(data=request.data)
            user = account.user

            password: str = redis_obj.get(user.username)
            if serialized.is_valid(raise_exception=True) and serialized.initial_data['password'] == password:
                redis_obj.delete(user.username)
                company: Company = Company.objects.create(account=account,
                                                          title=serialized.initial_data['title'],
                                                          industry=serialized.initial_data['industry'],
                                                          role=serialized.initial_data['role'],
                                                          people=serialized.initial_data['people'],
                                                          links=serialized.initial_data['links'])
                Profile.objects.create(account=account,
                                       company=company,
                                       uuid=token,
                                       name=account.user.username,
                                       email=email)

                # логинем самого пользователя в таблицу User
                login(request=request, user=user)

                # логинем аккаунт этого пользователя
                access_token = generate_access_token(user)
                refresh_token = generate_refresh_token(user)

                response = Response(data={'message': 'Профиль пользователя успешно зарегистрирован'},
                                    status=status.HTTP_200_OK)
                response.set_cookie(key='refreshtoken', value=refresh_token, httponly=True)
                response.data = {'access_token': access_token}
                return response
            else:
                return Response(data={'detail': 'Введенные данные не корректны или неверный пароль'},
                                status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            return Response(
                data={'detail': f'Что то пошло не так в ходе авторизации в системе. Убедитесь, что данные верны! {e}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    else:
        return Response(data={'detail': 'Что бы закончить регистрацию, расскажите о своей компании!'},
                        status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
@ensure_csrf_cookie  # принудительной отправки Django CSRF cookie в ответе в случае успешного входа в систему
def jwt_login_view(request) -> Response:
    """
    Аутентификация по JWT, вход в аккаунт
    """
    username: str = request.data.get('username')
    user = User.objects.get(username=username)
    response = Response()

    if username is None:
        raise exceptions.AuthenticationFailed('username required')
    if user is None:
        raise exceptions.AuthenticationFailed('user not found')

    account = Account.objects.get(user_id=user.id)
    serialized_account: Dict[str] = AccountSerializer(account).data

    access_token = generate_access_token(user)
    refresh_token = generate_refresh_token(user)

    # в файле cookie httponly, чтобы он не был доступен из клиентского javascript
    response.set_cookie(key='refreshtoken', value=refresh_token, httponly=True)
    response.data = {
        'access_token': access_token,
        'account': serialized_account,
    }

    return response


@api_view(['POST'])
@permission_classes([IsTokenValid])
def jwt_logout_view(request):
    refresh_token: Optional[str] = request.COOKIES.get('refreshtoken')
    BlackListedToken.objects.create(token=refresh_token, user=request.user)
    return Response({"message": "Вы успешно вышли с аккаунта"}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsTokenValid])
@csrf_protect
def refresh_token_view(request):  # протестировать на стороне клиента
    """
    Чтобы получить новый access_token, это представление ожидает 2 важных вещи:
    1. файл cookie, содержащий действительный refresh_token
    2. заголовок "ТОКЕН X-CSRF" с действительным токеном csrf,
     клиентское приложение может получить его из файлов cookie "csrftoken"
    """
    payload = get_payload(request)
    user = User.objects.get(id=payload['user_id'])
    access_token = generate_access_token(user)
    return Response(data={'access_token': access_token}, status=status.HTTP_200_OK)


class ProfileAccount(generics.RetrieveUpdateDestroyAPIView):
    """Класс профиля для каждого аккаунта пользователей"""
    serializer_class = ProfileSerializer
    permission_classes = (IsTokenValid,)
    queryset = Profile.objects.all()

    def get_object(self):
        try:
            profile: Profile = Profile.objects.get(uuid=self.kwargs['uuid'])
            return profile
        except Exception:
            raise Exception

    def get(self, request, *args, **kwargs):
        """Получаем профиль для текущего аккаунта"""
        try:
            profile: Profile = self.get_object()
            serialized = ProfileSerializer(profile)
            return Response(serialized.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(data={'detail': f"Профиля с таким uuid не существует, {e}"},
                            status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, *args, **kwargs):
        """Удаление профиля текущего пользователя"""
        user = self.request.user
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def patch(self, request, *args, **kwargs):
        """Обновление профиля текущего пользователя"""
        profile: Profile = self.get_object()
        serialized = ProfileSerializer(profile, data=request.data, partial=True)
        if serialized.is_valid():
            if request.data.get("name"):
                self.request.user.username = request.data.get("name")
            serialized.save()
            return Response(serialized.data, status=status.HTTP_200_OK)
        return Response({"message": "Данные не соответствуют ожидаемому формату и требованиям."},
                        status=status.HTTP_400_BAD_REQUEST)
