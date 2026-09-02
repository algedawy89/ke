"""
Shifts Serializers
"""
from rest_framework import serializers
from .models import Shift, ShiftSession


class ShiftSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    duration_hours = serializers.FloatField(read_only=True)
    is_currently_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Shift
        fields = [
            'id', 'name', 'shift_type', 'start_time', 'end_time',
            'branch', 'branch_name', 'is_active',
            'duration_hours', 'is_currently_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ShiftCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = ['name', 'shift_type', 'start_time', 'end_time', 'branch', 'is_active']


class ShiftSessionSerializer(serializers.ModelSerializer):
    shift_name = serializers.CharField(source='shift.name', read_only=True)
    cashier_name = serializers.CharField(source='cashier.full_name', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    closed_by_name = serializers.CharField(source='closed_by.full_name', read_only=True)
    reopened_by_name = serializers.CharField(source='reopened_by.full_name', read_only=True)
    can_edit_transactions = serializers.BooleanField(read_only=True)
    duration = serializers.CharField(read_only=True)

    class Meta:
        model = ShiftSession
        fields = [
            'id', 'shift', 'shift_name', 'cashier', 'cashier_name',
            'branch', 'branch_name', 'opened_at', 'closed_at',
            'status', 'closure_notes', 'closed_by', 'closed_by_name',
            'reopened_at', 'reopened_by', 'reopened_by_name', 'reopen_reason',
            'total_transactions', 'total_amount',
            'can_edit_transactions', 'duration',
            'created_at'
        ]
        read_only_fields = ['id', 'opened_at', 'created_at']


class ShiftSessionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShiftSession
        fields = ['shift', 'cashier', 'branch']


class ShiftCloseSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, allow_blank=True)


class ShiftReopenSerializer(serializers.Serializer):
    reason = serializers.CharField(required=True)
