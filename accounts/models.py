"""
Accounts Models - Users & Roles
"""
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import uuid

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User Model with Role-Based Access Control"""

    class Role(models.TextChoices):
        MANAGER = 'manager', _('المدير')
        SUPERVISOR = 'supervisor', _('المشرف')
        ACCOUNTANT = 'accountant', _('المحاسب')
        CASHIER = 'cashier', _('الكاشير')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('البريد الإلكتروني'), unique=True, blank=True, null=True)
    phone = models.CharField(_('رقم الهاتف'), max_length=20, unique=True)
    username = models.CharField(_('اسم المستخدم'), max_length=150, unique=True)
    full_name = models.CharField(_('الاسم الكامل'), max_length=255)
    role = models.CharField(_('الدور'), max_length=20, choices=Role.choices, default=Role.CASHIER)

    # Profile Images
    profile_image = models.ImageField(_('الصورة الشخصية'), upload_to='profiles/%Y/%m/', blank=True, null=True)
    id_card_front = models.ImageField(_('صورة البطاقة الأمامية'), upload_to='id_cards/%Y/%m/', blank=True, null=True)
    id_card_back = models.ImageField(_('صورة البطاقة الخلفية'), upload_to='id_cards/%Y/%m/', blank=True, null=True)

    # Status
    is_active = models.BooleanField(_('نشط'), default=True)
    is_staff = models.BooleanField(_('موظف'), default=False)
    is_superuser = models.BooleanField(_('مدير عام'), default=False)

    # Branch assignment (for cashiers)
    branch = models.ForeignKey(
        'branches.Branch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cashiers',
        verbose_name=_('الفرع')
    )

    # Timestamps
    date_joined = models.DateTimeField(_('تاريخ الانضمام'), default=timezone.now)
    last_login = models.DateTimeField(_('آخر دخول'), blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Created by
    created_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_users',
        verbose_name=_('تم الإنشاء بواسطة')
    )

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['full_name', 'phone']

    objects = UserManager()

    class Meta:
        verbose_name = _('مستخدم')
        verbose_name_plural = _('المستخدمين')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} ({self.get_role_display()})"

    @property
    def is_manager(self):
        return self.role == self.Role.MANAGER

    @property
    def is_supervisor(self):
        return self.role == self.Role.SUPERVISOR

    @property
    def is_accountant(self):
        return self.role == self.Role.ACCOUNTANT

    @property
    def is_cashier(self):
        return self.role == self.Role.CASHIER

    def can_manage_branches(self):
        return self.is_manager or self.is_supervisor

    def can_manage_wallets(self):
        return self.is_manager or self.is_supervisor

    def can_manage_users(self):
        return self.is_manager or self.is_supervisor

    def can_view_reports(self):
        return self.is_manager or self.is_accountant

    def can_create_transactions(self):
        return self.is_cashier and self.is_active and self.branch

    def get_permissions_list(self):
        """Return list of user permissions based on role"""
        permissions = {
            'manager': [
                'view_dashboard', 'manage_branches', 'manage_wallets',
                'manage_users', 'manage_shifts', 'view_reports',
                'manage_transactions', 'approve_edits', 'system_settings'
            ],
            'supervisor': [
                'view_dashboard', 'manage_branches', 'manage_wallets',
                'manage_cashiers', 'manage_shifts', 'view_reports',
                'approve_edits'
            ],
            'accountant': [
                'view_dashboard', 'view_reports', 'view_transactions',
                'export_reports', 'audit_transactions'
            ],
            'cashier': [
                'view_dashboard', 'create_transaction', 'edit_own_transaction',
                'delete_own_transaction', 'view_own_shifts'
            ]
        }
        return permissions.get(self.role, [])


class UserActivityLog(models.Model):
    """Track user activities for audit purposes"""

    class ActionType(models.TextChoices):
        LOGIN = 'login', _('تسجيل دخول')
        LOGOUT = 'logout', _('تسجيل خروج')
        CREATE = 'create', _('إنشاء')
        UPDATE = 'update', _('تعديل')
        DELETE = 'delete', _('حذف')
        VIEW = 'view', _('عرض')
        EXPORT = 'export', _('تصدير')
        APPROVE = 'approve', _('موافقة')
        REJECT = 'reject', _('رفض')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities', verbose_name=_('المستخدم'))
    action = models.CharField(_('الإجراء'), max_length=20, choices=ActionType.choices)
    entity_type = models.CharField(_('نوع الكيان'), max_length=50)
    entity_id = models.CharField(_('معرف الكيان'), max_length=100, blank=True)
    description = models.TextField(_('الوصف'), blank=True)
    ip_address = models.GenericIPAddressField(_('عنوان IP'), blank=True, null=True)
    user_agent = models.TextField(_('متصفح المستخدم'), blank=True)
    timestamp = models.DateTimeField(_('الوقت'), auto_now_add=True)

    class Meta:
        verbose_name = _('سجل النشاط')
        verbose_name_plural = _('سجلات الأنشطة')
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user} - {self.get_action_display()} - {self.timestamp}"
