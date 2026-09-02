"""
Wallets/E-Wallets Models
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid


class Wallet(models.Model):
    """Electronic Wallet Model"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('اسم المحفظة'), max_length=100)
    name_en = models.CharField(_('اسم المحفظة (إنجليزي)'), max_length=100, blank=True)

    # Wallet Code/Number
    wallet_code = models.CharField(_('كود المحفظة'), max_length=50, blank=True)
    phone_number = models.CharField(_('رقم المحفظة'), max_length=20, blank=True)

    # Logo
    logo = models.ImageField(_('الشعار'), upload_to='wallets/logos/%Y/%m/', blank=True, null=True)

    # Keywords for search/matching
    keywords = models.TextField(
        _('الكلمات المفتاحية'),
        help_text=_('أدخل الكلمات المفتاحية مفصولة بفواصل (مثال: جيب, jaib, محفظة جيب, jaib wallet)'),
        blank=True
    )

    # Branch
    branch = models.ForeignKey(
        'branches.Branch',
        on_delete=models.CASCADE,
        related_name='wallets',
        verbose_name=_('الفرع')
    )

    # Status
    is_active = models.BooleanField(_('نشطة'), default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_wallets'
    )

    class Meta:
        verbose_name = _('محفظة إلكترونية')
        verbose_name_plural = _('المحافظ الإلكترونية')
        ordering = ['-created_at']
        unique_together = ['name', 'branch']

    def __str__(self):
        return f"{self.name} - {self.branch.name}"

    @property
    def keywords_list(self):
        """Return keywords as a list"""
        if self.keywords:
            return [k.strip() for k in self.keywords.split(',') if k.strip()]
        return []

    @property
    def transactions_count(self):
        return self.transactions.count()

    @property
    def total_amount(self):
        from django.db.models import Sum
        result = self.transactions.aggregate(total=Sum('amount'))
        return result['total'] or 0

    def save(self, *args, **kwargs):
        # Auto-generate keywords if not provided
        if not self.keywords and self.name:
            auto_keywords = [self.name, self.name_en] if self.name_en else [self.name]
            if self.wallet_code:
                auto_keywords.append(self.wallet_code)
            self.keywords = ', '.join(filter(None, auto_keywords))
        super().save(*args, **kwargs)
