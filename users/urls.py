from django.urls import path

from .views import (ProfileAccount, ProfileMailList, jwt_login_view,
                    jwt_logout_view, refresh_token_view, registration, signin)

urlpatterns = [
    path('user/profile_mail/', ProfileMailList.as_view(), name='profile_mail_list'),
    path('user/registration/', registration, name='registration'),
    # это путь для аутентификации после регистрации
    path('user/signin/<str:email>/<uuid:token>/', signin, name='signin'),

    # это путь для аутентификации, когда пользователь длительное время не заходил в ЛК
    path('user/login/token/', jwt_login_view, name='jwt_login'),
    path('user/login/token/refresh/', refresh_token_view, name='token_refresh'),
    path('user/logout/token/', jwt_logout_view, name='jwt_logout'),

    path('user/profile/<uuid:uuid>/', ProfileAccount.as_view(), name='profile')
]
