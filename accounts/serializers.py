"""
Accounts Serializers
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """User Serializer"""
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    permissions = serializers.ListField(source='get_permissions_list', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'full_name', 'email', 'phone', 'role', 'role_display',
            'profile_image', 'id_card_front', 'id_card_back',
            'is_active', 'branch', 'branch_name', 'permissions',
            'date_joined', 'created_at'
        ]
        read_only_fields = ['id', 'date_joined', 'created_at']


class UserCreateSerializer(serializers.ModelSerializer):
    """User Create Serializer"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            'username', 'full_name', 'email', 'phone', 'password', 'password_confirm',
            'role', 'branch', 'profile_image', 'id_card_front', 'id_card_back',
            'is_active'
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "كلمات المرور غير متطابقة"})

        # Validate role permissions
        request = self.context.get('request')
        if request and request.user:
            creator_role = request.user.role
            new_role = attrs.get('role')

            # Supervisor can only create cashiers
            if creator_role == 'supervisor' and new_role not in ['cashier', 'accountant']:
                raise serializers.ValidationError(
                    {"role": "المشرف يمكنه إنشاء كواشير ومحاسبين فقط"}
                )

        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')

        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by'] = request.user

        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()

        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """User Update Serializer"""
    class Meta:
        model = User
        fields = [
            'full_name', 'email', 'phone', 'role', 'branch',
            'profile_image', 'id_card_front', 'id_card_back',
            'is_active'
        ]

    def validate_role(self, value):
        request = self.context.get('request')
        if request and request.user:
            if request.user.is_supervisor and value not in ['cashier', 'accountant']:
                raise serializers.ValidationError("المشرف يمكنه تعديل كواشير ومحاسبين فقط")
        return value


class CashierSerializer(serializers.ModelSerializer):
    """Cashier Serializer"""
    branch_name = serializers.CharField(source='branch.name', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'full_name', 'phone', 'profile_image',
            'id_card_front', 'id_card_back', 'branch', 'branch_name',
            'is_active', 'date_joined', 'last_login'
        ]


class CashierCreateSerializer(serializers.ModelSerializer):
    """Cashier Create Serializer"""
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            'username', 'full_name', 'phone', 'password',
            'branch', 'profile_image', 'id_card_front', 'id_card_back'
        ]

    def create(self, validated_data):
        password = validated_data.pop('password')

        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by'] = request.user

        user = User.objects.create(
            **validated_data,
            role='cashier'
        )
        user.set_password(password)
        user.save()

        return user


class ChangePasswordSerializer(serializers.Serializer):
    """Change Password Serializer"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password_confirm": "كلمات المرور غير متطابقة"})
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """User Profile Serializer"""
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    permissions = serializers.ListField(source='get_permissions_list', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'full_name', 'email', 'phone', 'role', 'role_display',
            'profile_image', 'branch', 'branch_name', 'permissions',
            'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'role', 'date_joined', 'last_login']
