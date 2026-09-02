"""
Transactions Serializers
"""
from rest_framework import serializers
from django.utils import timezone
from .models import Transaction, TransactionLog


class TransactionSerializer(serializers.ModelSerializer):
    wallet_name = serializers.CharField(source='wallet.name', read_only=True)
    wallet_logo = serializers.ImageField(source='wallet.logo', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    cashier_name = serializers.CharField(source='cashier.full_name', read_only=True)
    shift_session_name = serializers.CharField(source='shift_session.shift.name', read_only=True)
    is_editable = serializers.BooleanField(read_only=True)
    is_deletable = serializers.BooleanField(read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_id', 'amount', 'payment_time',
            'payment_reference', 'notes', 'notification_image',
            'wallet', 'wallet_name', 'wallet_logo',
            'branch', 'branch_name',
            'cashier', 'cashier_name',
            'shift_session', 'shift_session_name',
            'status', 'sync_status', 'is_offline', 'device_id',
            'is_edited', 'edited_at', 'edited_by', 'edit_reason',
            'is_deleted', 'deleted_at', 'deleted_by', 'deletion_reason',
            'is_editable', 'is_deletable',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'transaction_id', 'created_at', 'updated_at',
            'is_edited', 'edited_at', 'edited_by', 'edit_reason',
            'is_deleted', 'deleted_at', 'deleted_by', 'deletion_reason'
        ]


class TransactionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            'amount', 'payment_time', 'payment_reference', 'notes',
            'notification_image', 'wallet', 'shift_session'
        ]

    def validate(self, attrs):
        request = self.context.get('request')
        if request and request.user:
            attrs['cashier'] = request.user
            attrs['branch'] = request.user.branch
            attrs['created_by'] = request.user

            shift_session = attrs.get('shift_session')
            if shift_session and not shift_session.can_edit_transactions:
                raise serializers.ValidationError(
                    {"shift_session": "الوردية مغلقة، لا يمكن إضافة عمليات جديدة"}
                )
        return attrs


class TransactionUpdateSerializer(serializers.ModelSerializer):
    edit_reason = serializers.CharField(required=True)

    class Meta:
        model = Transaction
        fields = ['amount', 'payment_time', 'payment_reference', 'notes', 
                  'notification_image', 'wallet', 'edit_reason']

    def validate(self, attrs):
        request = self.context.get('request')
        if request and request.user:
            instance = self.instance
            if instance and not instance.is_editable:
                raise serializers.ValidationError(
                    {"detail": "لا يمكن تعديل هذه العملية"}
                )
        return attrs

    def update(self, instance, validated_data):
        edit_reason = validated_data.pop('edit_reason', '')
        old_data = {
            'amount': str(instance.amount),
            'payment_time': instance.payment_time.isoformat(),
            'payment_reference': instance.payment_reference,
            'notes': instance.notes,
            'wallet': str(instance.wallet.id) if instance.wallet else None
        }

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.is_edited = True
        instance.edited_at = timezone.now()
        instance.edited_by = self.context['request'].user
        instance.edit_reason = edit_reason
        instance.save()

        TransactionLog.objects.create(
            transaction=instance,
            action='update',
            user=self.context['request'].user,
            old_data=old_data,
            new_data=validated_data
        )
        return instance


class TransactionDeleteSerializer(serializers.Serializer):
    reason = serializers.CharField(required=True)
