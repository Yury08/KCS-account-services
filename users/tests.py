import logging
from typing import Dict
from unittest.mock import patch

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from .models import Account, Company, Profile, ProfileMail

logger = logging.getLogger(__name__)
BASE_URL = "http://localhost:8001"


class ProfileMailTests(APITestCase):
    @staticmethod
    def add_profile_mail() -> None:
        """Добавляем запись в таблицу ProfileMail"""
        logger.debug('Adding a new record into database')
        p = ProfileMail(email_name_profile="test",
                        email_host="localhost",
                        email_host_password='Nastya_1337',
                        email_host_user="Yuri")
        p.save()
        logger.debug('Successfully added test mail_profile into the database')

    def test_list_profile_mail(self) -> None:
        """Тестируем вывод всех записей из таблицы ProfileMail"""
        logger.debug('Starting test list profile mail')

        self.add_profile_mail()

        self.user = User.objects.create_user(username="Test user")
        self.client.force_authenticate(self.user)

        url = f"{BASE_URL}/api/user/profile_mail/"

        logger.debug(f"Sending TEST data to url: {url}")
        response = self.client.get(url, format='json')
        json_obj = response.json()

        logger.debug(f'Testing status code response: {json_obj}, code: {response.status_code}')
        # не тестирую разрешение для admin юзеров
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        logger.debug('Testing result count')
        self.assertEqual(len(json_obj), 1)


class RegistrationTests(APITestCase):
    @patch('users.views.MessageMail')
    @patch('users.views.MailCenter')
    @patch('asyncio.ensure_future')
    def test_create_user(self, mock_ensure_future, mock_mail_center, mock_message_mail) -> None:
        """Тестирование регистрации пользователей в системе"""
        logger.debug("Starting test create user")

        url: str = f"{BASE_URL}/api/user/registration/"
        username: str = "Yuri08"
        email: str = "ukravzov@mail.ru"

        data: Dict[str, str] = {
            "username": username,
            "email": email
        }

        logger.debug(f"Setting test data to url {url}")
        response = self.client.post(url, data, format='json')

        logger.debug(f"Testing status response: {response.json()} code: {response.status_code}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        logger.debug("Testing user count to make sure obj was success added")
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Account.objects.count(), 1)

    # def test_signin(self) -> None:
    #     """Тестирование создания записи в таблице Profile и Company"""
    #     logger.debug("Starting test signin user")
    #
    #     email: str = "ukravzov@mail.ru"
    #     token: uuid = uuid.uuid4()
    #     url = reverse('signin', kwargs={'email': email, 'token': token})
    #
    #     T = TypeVar('T')
    #
    #     data: Dict[str, T] = {"title": "Google",
    #                           "industry": "IT",
    #                           "role": "Генеральный директор",
    #                           "people": 100,
    #                           "links": {"vk": "https://vk.com"}}
    #
    #     logger.debug(f"Setting test data to url {url}")
    #     response = self.client.post(url, data, format='json')
    #
    #     logger.debug(f"Testing status response: {response.json()} code: {response.status_code}")
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #
    #     logger.debug("Testing user count to make sure obj was success added")
    #     self.assertEqual(Company.objects.count(), 1)
    #     self.assertEqual(Profile.objects.count(), 1)


class ProfileAccountTests(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(username='Test user')
        self.account = Account.objects.create(user=self.user, name="Test User",
                                              token="fe507723-e45d-403f-92dc-a203ad110c1b")
        self.company = Company.objects.create(account=self.account, title='Google',
                                              industry='test', role='test', people=10)
        self.profile = Profile.objects.create(account=self.account,
                                              company=self.company,
                                              uuid='a7e05322-11f8-40af-a44c-28ad6790904a',
                                              name='Test User',
                                              email='test@example.com')
        self.client.force_authenticate(self.user)

        self.url = reverse('profile', kwargs={'uuid': self.profile.uuid})

    def test_get_profile(self):
        logger.debug("Starting test get profile user")
        logger.debug(f"Sending request to url {self.url}")
        response = self.client.get(self.url)

        logger.debug("Testing status response code")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test User')
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['uuid'], 'a7e05322-11f8-40af-a44c-28ad6790904a')

    def test_get_profile_invalid_uuid(self):
        url = reverse('profile', kwargs={'uuid': 'a7e05322-11f8-40af-a44c-28ad6790904b'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_profile(self):
        logger.debug("Sending request to delete profile")
        response = self.client.delete(self.url)
        logger.debug("Testing status response code")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_update_profile(self):
        logger.debug("Starting test update profile user")
        data: Dict[str] = {"name": "New test name", "email": "new_test@mail.ru", "password": "Nastya_1337"}

        logger.debug("Sending request to update profile")
        response = self.client.put(self.url, data=data, format='json')

        logger.debug(f"Testing status response: {response.json()} code: {response.status_code}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class LoginJWTTests(APITestCase):
    """"""
    # def set_token(self):
    #     self.user = User.objects.create_user(username="Test")
    #     self.account: Account = Account.objects.create(user=self.user)
    #     self.refresh_token: str = generate_refresh_token(self.account)
    #     self.client.cookies.setdefault('refreshtoken', self.refresh_token)
    #
    # def test_refresh_token_view(self):
    #     self.set_token()
    #     logger.debug("Starting test login with JWT")
    #     client = APIClient()
    #     response = self.client.get(f'{BASE_URL}/api/user/login/token/refresh/')
    #
    #     logger.debug("Getting refresh_token and csrf_token from cookie")
    #     refresh_token: str = self.client.cookies['refreshtoken'].value
    #
    #     csrf_token: str = response.client.cookies['csrftoken']
    #     if refresh_token:
    #         response = client.post(f'{BASE_URL}/api/user/login/token/refresh/', HTTP_X_CSRFTOKEN=csrf_token)
    #
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
