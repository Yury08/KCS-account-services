import json
import uuid as uuid
from datetime import datetime
from typing import Dict, List

from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import JSONField
from django.db.models.fields import Field
from PIL import Image

USER_ROLE: List[tuple[str, str]] = [
    ("ген. директор", 'Генеральный директор'),
    ("менеджер", 'Менеджер'),
    ("it спец.", 'IT специалист'),
    ("руководитель отдела", 'Руководитель отдела'),
    ("другое", 'Другое'),
]

INDUSTRY: List[tuple[str, str]] = [
    ("отп. и розн. т", "Оптовая и розничная торговля"),
    ("it", "IT"),
    ("трен. и консалт.", "Тренинг, консалтинг"),
    ("туризм", "Туризм"),
    ("промышленность", "Промышленность"),
    ("маркет. и реклама", "Маркетинг, реклама"),
    ("другое", "Другое")
]


class Account(models.Model):
    """Аккаунт пользователя для хранения базовой информации"""
    user: User = models.ForeignKey(User, on_delete=models.CASCADE)
    is_admin: bool = models.BooleanField(default=False)
    token: str = models.CharField(max_length=255, default=str(uuid.uuid4()))

    class Meta:
        verbose_name = "Аккаунт"
        verbose_name_plural = "Аккаунты"

    def __str__(self):
        return f"Аккаунт пользователя {self.user.username}"


def default_links() -> Dict[str, str]:
    return {'telegram': '', 'instagram': '', 'linkedin': '', 'vk': ''}


class Company(models.Model):
    """Компания"""
    account: Account = models.ForeignKey(Account, on_delete=models.CASCADE)
    title: str = models.CharField(max_length=255)
    industry: str = models.CharField(choices=INDUSTRY, max_length=255)
    role: str = models.CharField(choices=USER_ROLE, max_length=255)
    people: int = models.IntegerField()
    links: json = JSONField(default=default_links)

    class Meta:
        verbose_name = "Компания"
        verbose_name_plural = "Компании"

    def __str__(self):
        return f"Пользователь {self.account.user.username} связан с компанией {self.title}"


class Profile(models.Model):
    """Профиль пользователя"""
    account: Account = models.ForeignKey(Account, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True)
    uuid: uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True)
    name: str = models.CharField(max_length=255)
    image = models.ImageField(default='default/default.jpg', upload_to='user_images')
    email: str = models.EmailField()

    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Please enter a valid phone number")
    phone: str = models.CharField(validators=[phone_regex], max_length=17, blank=True, null=True)
    created: datetime = models.DateTimeField(auto_now_add=True)
    updated: datetime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Профиль пользователя {self.name} связан с аккаунтом {self.account.id}'

    def save(self, *args, **kwargs) -> None:
        """
        Обрезает изображение пользователя
        """
        super().save()

        image: Image = Image.open(self.image.path)

        if image.height > 256 or image.width > 256:
            resize: tuple[int] = (256, 256)
            image.thumbnail(resize)
            image.save(self.image.path)

    class Meta:
        verbose_name = 'Профаил'
        verbose_name_plural = 'Профайлы'


class BlackListedToken(models.Model):
    token = models.CharField(max_length=500)
    user = models.ForeignKey(User, related_name="token_user", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("token", "user")


class ProfileMail(models.Model):
    """Профиль почты"""
    id: int = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email_act_profile: bool = models.BooleanField(default=False)
    email_name_profile: str = models.CharField(max_length=255)
    email_backend: str = models.CharField(max_length=255, default='django.core.mail.backends.smtp.EmailBackend')
    email_file_path: Field = models.FileField(blank=True, null=True)
    email_host: str = models.CharField(max_length=255)
    email_host_password: str = models.CharField(max_length=255)
    email_host_user: str = models.CharField(max_length=255)
    email_port: int = models.IntegerField(default=0)
    email_subject_prefix: str = models.CharField(max_length=255, blank=True, null=True)
    email_use_localtime: bool = models.BooleanField(default=False)
    email_use_tls: bool = models.BooleanField(default=True)
    email_use_ssl: bool = models.BooleanField(default=False)
    email_ssl_certfile: Field = models.FileField(default=None, blank=True, null=True)
    email_ssl_keyfile: Field = models.FileField(default=None, blank=True, null=True)
    email_timeout: int = models.IntegerField(default=0)
    email_from_email: str = models.CharField(default='', max_length=255)

    class Meta:
        verbose_name = 'Профиль почтового центра'
        verbose_name_plural = 'Профили почтового центра'
        db_table = 'rs_platform_mails_profile'
        ordering = ['email_name_profile', ]

    def __str__(self):
        return f'{self.email_name_profile} - {self.id}'
