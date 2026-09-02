"""
Wallets Serializers
"""
from rest_framework import serializers
from .models import Wallet


class WalletSerializer(serializers.ModelSerializer):
    """Wallet Serializer"""
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    keywords_list = serializers.ListField(read_only=True)
    transactions_count = serializers.IntegerField(read_only=True)
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = Wallet
        fields = [
            'id', 'name', 'name_en', 'wallet_code', 'phone_number',
            'logo', 'keywords', 'keywords_list',
            'branch', 'branch_name', 'is_active',
            'transactions_count', 'total_amount',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class WalletCreateUpdateSerializer(serializers.ModelSerializer):
    """Wallet Create/Update Serializer"""
    class Meta:
        model = Wallet
        fields = [
            'name', 'name_en', 'wallet_code', 'phone_number',
            'logo', 'keywords', 'branch', 'is_active'
        ]

    def validate(self, attrs):
        branch = attrs.get('branch')
        name = attrs.get('name')

        if branch and name:
            if self.instance and self.instance.branch == branch and self.instance.name == name:
                return attrs
            if Wallet.objects.filter(branch=branch, name=name).exists():
                raise serializers.ValidationError(
                    {"name": "يوجد محفظة بنفس الاسم في هذا الفرع"}
                )
        return attrs


class WalletListSerializer(serializers.ModelSerializer):
    """Wallet List Serializer (lightweight)"""
    branch_name = serializers.CharField(source='branch.name', read_only=True)

    class Meta:
        model = Wallet
        fields = ['id', 'name', 'name_en', 'logo', 'branch_name', 'is_active']


class WalletSearchSerializer(serializers.Serializer):
    """Wallet Search Serializer"""
    query = serializers.CharField(required=True, max_length=100)
    branch = serializers.UUIDField(required=False)
