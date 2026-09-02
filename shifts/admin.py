from django.contrib import admin
from .models import Shift, ShiftSession

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ['name', 'branch', 'shift_type', 'start_time', 'end_time', 'is_active']
    list_filter = ['shift_type', 'is_active', 'branch']

@admin.register(ShiftSession)
class ShiftSessionAdmin(admin.ModelAdmin):
    list_display = ['shift', 'cashier', 'status', 'opened_at', 'total_amount']
    list_filter = ['status', 'opened_at']