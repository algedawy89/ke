"""
Branches Serializers
"""
from rest_framework import serializers
from .models import Branch


class BranchSerializer(serializers.ModelSerializer):
    """Branch Serializer"""
    manager_name = serializers.CharField(source='manager.full_name', read_only=True)
    active_cashiers_count = serializers.IntegerField(read_only=True)
    wallets_count = serializers.IntegerField(read_only=True)
    today_transactions_count = serializers.IntegerField(read_only=True)
    today_total_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = Branch
        fields = [
            'id', 'name',  'address', 'phone', 
              'is_active', 'manager', 'manager_name',
            'active_cashiers_count', 'wallets_count',
            'today_transactions_count', 'today_total_amount',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BranchCreateUpdateSerializer(serializers.ModelSerializer):
    """Branch Create/Update Serializer"""
    class Meta:
        model = Branch
        fields = [
            'name','address', 'phone', 'email',
            'is_active', 'manager'
        ]

    # def validate_code(self, value):
    #     if self.instance and self.instance.code == value:
    #         return value
    #     if Branch.objects.filter(code=value).exists():
    #         raise serializers.ValidationError("كود الفرع مستخدم بالفعل")
    #     return value


class BranchListSerializer(serializers.ModelSerializer):
    """Branch List Serializer (lightweight)"""
    manager_name = serializers.CharField(source='manager.full_name', read_only=True)

    class Meta:
        model = Branch
        fields = ['id', 'name', 'is_active', 'manager_name']
