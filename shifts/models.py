"""
Shifts Models - Work Shifts Management
"""
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import uuid


class Shift(models.Model):
    """Work Shift Configuration for each Branch"""

    class ShiftType(models.TextChoices):
        MORNING = 'morning', _('وردية صباحية')
        EVENING = 'evening', _('وردية مسائية')
        NIGHT = 'night', _('وردية ليلية')
        CUSTOM = 'custom', _('وردية مخصصة')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('اسم الوردية'), max_length=100)
    shift_type = models.CharField(_('نوع الوردية'), max_length=20, choices=ShiftType.choices, default=ShiftType.MORNING)

    # Time Configuration
    start_time = models.TimeField(_('وقت البدء'))
    end_time = models.TimeField(_('وقت الانتهاء'))

    # Branch
    branch = models.ForeignKey(
        'branches.Branch',
        on_delete=models.CASCADE,
        related_name='shifts',
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
        related_name='created_shifts'
    )

    class Meta:
        verbose_name = _('وردية عمل')
        verbose_name_plural = _('ورديات العمل')
        ordering = ['start_time']

    def __str__(self):
        return f"{self.name} ({self.branch.name}) - {self.start_time.strftime('%H:%M')} إلى {self.end_time.strftime('%H:%M')}"

    @property
    def duration_hours(self):
        """Calculate shift duration in hours"""
        from datetime import datetime
        start = datetime.combine(datetime.today(), self.start_time)
        end = datetime.combine(datetime.today(), self.end_time)
        if end < start:
            end = datetime.combine(datetime.today(), self.end_time)
            end += timezone.timedelta(days=1)
        diff = end - start
        return diff.total_seconds() / 3600

    @property
    def is_currently_active(self):
        """Check if shift is currently active based on time"""
        now = timezone.now().time()
        if self.start_time <= self.end_time:
            return self.start_time <= now <= self.end_time
        else:
            return now >= self.start_time or now <= self.end_time


class ShiftSession(models.Model):
    """Actual Shift Session - tracks when a cashier starts and ends their shift"""

    class Status(models.TextChoices):
        OPEN = 'open', _('مفتوحة')
        CLOSED = 'closed', _('مغلقة')
        PENDING_APPROVAL = 'pending', _('بانتظار المراجعة')
        REOPENED = 'reopened', _('تم إعادة فتحها')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Shift Configuration
    shift = models.ForeignKey(
        Shift,
        on_delete=models.PROTECT,
        related_name='sessions',
        verbose_name=_('الوردية')
    )

    # Cashier
    cashier = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='shift_sessions',
        verbose_name=_('الكاشير'),
        limit_choices_to={'role': 'cashier'}
    )

    # Branch
    branch = models.ForeignKey(
        'branches.Branch',
        on_delete=models.PROTECT,
        related_name='shift_sessions',
        verbose_name=_('الفرع')
    )

    # Session Times
    opened_at = models.DateTimeField(_('وقت الفتح'), auto_now_add=True)
    closed_at = models.DateTimeField(_('وقت الإغلاق'), blank=True, null=True)

    # Status
    status = models.CharField(_('الحالة'), max_length=20, choices=Status.choices, default=Status.OPEN)

    # Closure Details
    closure_notes = models.TextField(_('ملاحظات الإغلاق'), blank=True)
    closed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='closed_sessions',
        verbose_name=_('تم الإغلاق بواسطة')
    )

    # Reopen Details
    reopened_at = models.DateTimeField(_('وقت إعادة الفتح'), blank=True, null=True)
    reopened_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reopened_sessions',
        verbose_name=_('تم إعادة الفتح بواسطة')
    )
    reopen_reason = models.TextField(_('سبب إعادة الفتح'), blank=True)

    # Calculated Fields
    total_transactions = models.PositiveIntegerField(_('إجمالي العمليات'), default=0)
    total_amount = models.DecimalField(_('إجمالي المبالغ'), max_digits=15, decimal_places=2, default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('جلسة وردية')
        verbose_name_plural = _('جلسات الورديات')
        ordering = ['-opened_at']

    def __str__(self):
        return f"{self.shift.name} - {self.cashier.full_name} - {self.opened_at.strftime('%Y-%m-%d %H:%M')}"

    @property
    def duration(self):
        """Calculate session duration"""
        end = self.closed_at or timezone.now()
        diff = end - self.opened_at
        hours = diff.total_seconds() // 3600
        minutes = (diff.total_seconds() % 3600) // 60
        return f"{int(hours)}:{int(minutes):02d}"

    @property
    def can_edit_transactions(self):
        """Check if transactions can be edited"""
        return self.status in [self.Status.OPEN, self.Status.REOPENED]

    def close(self, user, notes=''):
        """Close the shift session"""
        from django.db.models import Sum, Count

        self.status = self.Status.CLOSED
        self.closed_at = timezone.now()
        self.closed_by = user
        self.closure_notes = notes

        # Calculate totals
        totals = self.transactions.aggregate(
            count=Count('id'),
            total=Sum('amount')
        )
        self.total_transactions = totals['count'] or 0
        self.total_amount = totals['total'] or 0

        self.save()

    def reopen(self, user, reason=''):
        """Reopen the shift session (by supervisor/manager)"""
        self.status = self.Status.REOPENED
        self.reopened_at = timezone.now()
        self.reopened_by = user
        self.reopen_reason = reason
        self.save()
