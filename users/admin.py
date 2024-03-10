from django.contrib import admin

from .models import Account, BlackListedToken, Company, Profile, ProfileMail

admin.site.register(Profile)
admin.site.register(Account)
admin.site.register(Company)
admin.site.register(ProfileMail)
admin.site.register(BlackListedToken)
