from django.contrib import admin
from .models import Transaction, TransactionLog

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'amount', 'wallet', 'cashier', 'status', 'created_at']
    list_filter = ['status', 'is_deleted', 'created_at', 'wallet']
    search_fields = ['transaction_id', 'payment_reference']

@admin.register(TransactionLog)
class TransactionLogAdmin(admin.ModelAdmin):
    list_display = ['transaction', 'action', 'user', 'timestamp']
    list_filter = ['action', 'timestamp']   