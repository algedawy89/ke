"""
Transactions Models - Payment Records
"""
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import uuid


class Transaction(models.Model):
    """Payment Transaction Record"""

    class Status(models.TextChoices):
        PENDING = 'pending', _('معلقة')
        COMPLETED = 'completed', _('مكتملة')
        CANCELLED = 'cancelled', _('ملغاة')
        REFUNDED = 'refunded', _('مسترجعة')

    class SyncStatus(models.TextChoices):
        SYNCED = 'synced', _('متزامن')
        PENDING_SYNC = 'pending', _('بانتظار المزامنة')
        FAILED = 'failed', _('فشلت المزامنة')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Unique Transaction ID (for offline/online sync)
    transaction_id = models.CharField(
        _('معرف العملية'),
        max_length=100,
        unique=True,
        editable=False
    )

    # Amount
    amount = models.DecimalField(_('المبلغ'), max_digits=15, decimal_places=2)

    # Payment Details
    payment_time = models.DateTimeField(_('وقت الدفع'), default=timezone.now)
    payment_reference = models.CharField(_('رقم مرجعي'), max_length=100, blank=True)
    notes = models.TextField(_('ملاحظات'), blank=True)

    # Payment Notification Image
    notification_image = models.ImageField(
        _('صورة إشعار الدفع'),
        upload_to='transactions/notifications/%Y/%m/%d/',
        blank=True,
        null=True
    )

    # Relationships
    wallet = models.ForeignKey(
        'wallets.Wallet',
        on_delete=models.PROTECT,
        related_name='transactions',
        verbose_name=_('المحفظة')
    )

    branch = models.ForeignKey(
        'branches.Branch',
        on_delete=models.PROTECT,
        related_name='transactions',
        verbose_name=_('الفرع')
    )

    cashier = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='transactions',
        verbose_name=_('الكاشير'),
        limit_choices_to={'role': 'cashier'}
    )

    shift_session = models.ForeignKey(
        'shifts.ShiftSession',
        on_delete=models.PROTECT,
        related_name='transactions',
        verbose_name=_('جلسة الوردية')
    )

    # Status
    status = models.CharField(_('الحالة'), max_length=20, choices=Status.choices, default=Status.COMPLETED)
    sync_status = models.CharField(_('حالة المزامنة'), max_length=20, choices=SyncStatus.choices, default=SyncStatus.SYNCED)

    # Offline/Online tracking
    is_offline = models.BooleanField(_('تمت بدون اتصال'), default=False)
    device_id = models.CharField(_('معرف الجهاز'), max_length=100, blank=True)
    synced_at = models.DateTimeField(_('وقت المزامنة'), blank=True, null=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_transactions'
    )

    # Edit tracking
    is_edited = models.BooleanField(_('تم التعديل'), default=False)
    edited_at = models.DateTimeField(_('وقت التعديل'), blank=True, null=True)
    edited_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='edited_transactions',
        verbose_name=_('تم التعديل بواسطة')
    )
    edit_reason = models.TextField(_('سبب التعديل'), blank=True)

    # Deletion tracking (soft delete)
    is_deleted = models.BooleanField(_('محذوف'), default=False)
    deleted_at = models.DateTimeField(_('وقت الحذف'), blank=True, null=True)
    deleted_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deleted_transactions',
        verbose_name=_('تم الحذف بواسطة')
    )
    deletion_reason = models.TextField(_('سبب الحذف'), blank=True)

    class Meta:
        verbose_name = _('عملية دفع')
        verbose_name_plural = _('عمليات الدفع')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['created_at']),
            models.Index(fields=['cashier', 'created_at']),
            models.Index(fields=['branch', 'created_at']),
            models.Index(fields=['wallet', 'created_at']),
            models.Index(fields=['shift_session']),
        ]

    def __str__(self):
        return f"{self.transaction_id} - {self.amount} - {self.wallet.name}"

    def save(self, *args, **kwargs):
        # Generate unique transaction ID if not set
        if not self.transaction_id:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            random_suffix = str(uuid.uuid4())[:8].upper()
            self.transaction_id = f"TXN-{timestamp}-{random_suffix}"
        super().save(*args, **kwargs)

    def soft_delete(self, user, reason=''):
        """Soft delete the transaction"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.deletion_reason = reason
        self.status = self.Status.CANCELLED
        self.save()

    def restore(self, user):
        """Restore a soft-deleted transaction"""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.deletion_reason = ''
        self.status = self.Status.COMPLETED
        self.save()

    @property
    def is_editable(self):
        """Check if transaction can be edited"""
        if self.is_deleted:
            return False
        if self.shift_session and not self.shift_session.can_edit_transactions:
            return False
        return True

    @property
    def is_deletable(self):
        """Check if transaction can be deleted"""
        return self.is_editable


class TransactionLog(models.Model):
    """Transaction Audit Log"""

    class Action(models.TextChoices):
        CREATE = 'create', _('إنشاء')
        UPDATE = 'update', _('تعديل')
        DELETE = 'delete', _('حذف')
        RESTORE = 'restore', _('استعادة')
        VIEW = 'view', _('عرض')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name=_('العملية')
    )
    action = models.CharField(_('الإجراء'), max_length=20, choices=Action.choices)
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('المستخدم')
    )
    old_data = models.JSONField(_('البيانات القديمة'), blank=True, null=True)
    new_data = models.JSONField(_('البيانات الجديدة'), blank=True, null=True)
    timestamp = models.DateTimeField(_('الوقت'), auto_now_add=True)
    ip_address = models.GenericIPAddressField(_('عنوان IP'), blank=True, null=True)

    class Meta:
        verbose_name = _('سجل عملية')
        verbose_name_plural = _('سجلات العمليات')
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.transaction.transaction_id} - {self.get_action_display()}"
