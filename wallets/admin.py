from django.contrib import admin
from .models import Wallet

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['name', 'branch', 'wallet_code', 'is_active']
    list_filter = ['is_active', 'branch']
    search_fields = ['name', 'name_en', 'wallet_code', 'keywords']