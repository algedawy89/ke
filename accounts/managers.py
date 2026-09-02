"""
Custom User Manager
"""
from django.contrib.auth.models import BaseUserManager
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    def create_user(self, username, full_name, phone, password=None, **extra_fields):
        if not username:
            raise ValueError(_('يجب إدخال اسم المستخدم'))
        if not full_name:
            raise ValueError(_('يجب إدخال الاسم الكامل'))
        if not phone:
            raise ValueError(_('يجب إدخال رقم الهاتف'))

        user = self.model(
            username=username,
            full_name=full_name,
            phone=phone,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, full_name, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'manager')

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(username, full_name, phone, password, **extra_fields)
