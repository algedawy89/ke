from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserActivityLog

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'full_name', 'phone', 'role', 'branch', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'branch', 'date_joined']
    search_fields = ['username', 'full_name', 'phone', 'email']
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('معلومات شخصية', {'fields': ('full_name', 'email', 'phone', 'profile_image')}),
        ('الدور والفرع', {'fields': ('role', 'branch')}),
        ('البطاقة الشخصية', {'fields': ('id_card_front', 'id_card_back')}),
        ('الصلاحيات', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('تواريخ', {'fields': ('last_login', 'date_joined')}),
    )

@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'entity_type', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['user__username', 'description']