"""
Branches Models
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid


class Branch(models.Model):
    """Restaurant Branch Model"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('اسم الفرع'), max_length=255)
    # code = models.CharField(_('كود الفرع'), max_length=50, unique=True)
    address = models.TextField(_('العنوان'), blank=True)
    phone = models.CharField(_('هاتف الفرع'), max_length=20, blank=True)
    # email = models.EmailField(_('البريد الإلكتروني'), blank=True)

    # Location
    # city = models.CharField(_('المدينة'), max_length=100, blank=True)
    # region = models.CharField(_('المنطقة'), max_length=100, blank=True)

    # Status
    is_active = models.BooleanField(_('نشط'), default=True)

    # Manager
    manager = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_branches',
        verbose_name=_('مدير الفرع'),
        limit_choices_to={'role': 'supervisor'}
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_branches'
    )

    class Meta:
        verbose_name = _('فرع')
        verbose_name_plural = _('الفروع')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.code})"

    @property
    def active_cashiers_count(self):
        return self.cashiers.filter(is_active=True).count()

    @property
    def wallets_count(self):
        # إذا تم حساب القيمة من خلال annotate في الـ View أو Serializer
        if hasattr(self, '_wallets_count'):
            return self._wallets_count
        # إذا لم تُحسب، قم بحسابها كالمعتاد
        return self.wallets.filter(is_active=True).count()

    @wallets_count.setter
    def wallets_count(self, value):
        # السماح لـ Django بتعيين النتيجة المحسوبة من annotate
        self._wallets_count = value

    @property
    def today_transactions_count(self):
        from django.utils import timezone
        from transactions.models import Transaction
        today = timezone.now().date()
        return Transaction.objects.filter(
            branch=self,
            created_at__date=today
        ).count()

    @property
    def today_total_amount(self):
        from django.utils import timezone
        from transactions.models import Transaction
        from django.db.models import Sum
        today = timezone.now().date()
        result = Transaction.objects.filter(
            branch=self,
            created_at__date=today
        ).aggregate(total=Sum('amount'))
        return result['total'] or 0
