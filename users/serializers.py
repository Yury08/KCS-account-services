from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Account, Company, Profile, ProfileMail


class UserSerializer(serializers.ModelSerializer):
    """Сериализация модели User"""

    class Meta:
        model = User
        fields = ('username', 'email')


class AccountSerializer(serializers.ModelSerializer):
    """Сериализация модели Account"""
    user: User = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Account
        fields = '__all__'


class CompanySerializer(serializers.ModelSerializer):
    """Сериализация модели Company"""

    class Meta:
        model = Company
        # если вдруг что то не будет работать при вызове функции signin, то здесь надо вернуть account
        fields = ('title', 'industry', 'role', 'people', 'links')


class ProfileSerializer(serializers.ModelSerializer):
    """Сериализация модели Profile"""
    user: User = serializers.HiddenField(default=serializers.CurrentUserDefault())
    company: Company = CompanySerializer(many=False)

    class Meta:
        model = Profile
        fields = ('user', 'uuid', 'name', 'image', 'email', 'phone', 'created', 'updated', 'company')

    def update(self, instance, validated_data):
        company_data = validated_data.pop('company', {})
        instance = super().update(instance, validated_data)
        for field, value in company_data.items():
            setattr(instance.company, field, value)
        return instance


class ProfileMailSerializer(serializers.ModelSerializer):
    """Сериализация модели ProfileMail"""

    class Meta:
        model = ProfileMail
        fields = '__all__'
