"""
Accounts Views
"""
from rest_framework import generics, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend

from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    CashierSerializer, CashierCreateSerializer, ChangePasswordSerializer,
    UserProfileSerializer
)
from .permissions import (
    IsManager, IsSupervisor, IsManagerOrSupervisor,
    CanManageUsers, IsCashier
)

User = get_user_model()


class UserListView(generics.ListAPIView):
    """List all users - Manager & Supervisor only"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsManagerOrSupervisor]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'is_active', 'branch']
    search_fields = ['full_name', 'username', 'phone', 'email']
    ordering_fields = ['created_at', 'full_name', 'role']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_manager:
            return User.objects.all()
        elif user.is_supervisor:
            # Supervisor sees only cashiers in their managed branches
            return User.objects.filter(role='cashier', branch__manager=user)
        return User.objects.none()


class UserDetailView(generics.RetrieveAPIView):
    """Retrieve user details"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'


class UserCreateView(generics.CreateAPIView):
    """Create new user - Manager & Supervisor"""
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [CanManageUsers]


class UserUpdateView(generics.UpdateAPIView):
    """Update user - Manager & Supervisor"""
    queryset = User.objects.all()
    serializer_class = UserUpdateSerializer
    permission_classes = [CanManageUsers]
    lookup_field = 'pk'


class UserDeleteView(generics.DestroyAPIView):
    """Soft delete user (deactivate) - Manager & Supervisor"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [CanManageUsers]
    lookup_field = 'pk'

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


class CashierListView(generics.ListAPIView):
    """List all cashiers"""
    serializer_class = CashierSerializer
    permission_classes = [IsManagerOrSupervisor]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_active', 'branch']
    search_fields = ['full_name', 'username', 'phone']

    def get_queryset(self):
        user = self.request.user
        if user.is_manager:
            return User.objects.filter(role='cashier')
        elif user.is_supervisor:
            return User.objects.filter(role='cashier', branch__manager=user)
        return User.objects.none()


class CashierCreateView(generics.CreateAPIView):
    """Create new cashier"""
    queryset = User.objects.all()
    serializer_class = CashierCreateSerializer
    permission_classes = [IsManagerOrSupervisor]


class CashierUpdateView(generics.UpdateAPIView):
    """Update cashier"""
    queryset = User.objects.filter(role='cashier')
    serializer_class = CashierSerializer
    permission_classes = [IsManagerOrSupervisor]
    lookup_field = 'pk'


class CashierToggleActiveView(generics.GenericAPIView):
    """Toggle cashier active status"""
    queryset = User.objects.filter(role='cashier')
    permission_classes = [IsManagerOrSupervisor]

    def post(self, request, pk=None):
        try:
            cashier = self.get_queryset().get(pk=pk)
            cashier.is_active = not cashier.is_active
            cashier.save()
            status_text = 'مفعل' if cashier.is_active else 'معطل'
            return Response(
                {'message': f'تم {status_text} الكاشير بنجاح', 'is_active': cashier.is_active},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response({'error': 'الكاشير غير موجود'}, status=status.HTTP_404_NOT_FOUND)


class UserProfileView(generics.RetrieveAPIView):
    """Get current user profile"""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(generics.GenericAPIView):
    """Change password"""
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {'old_password': ['كلمة المرور الحالية غير صحيحة']},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(serializer.validated_data['new_password'])
        user.save()

        return Response({'message': 'تم تغيير كلمة المرور بنجاح'}, status=status.HTTP_200_OK)


class DashboardStatsView(generics.GenericAPIView):
    """Dashboard statistics"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        stats = {}

        if user.is_manager:
            stats = {
                'total_branches': user.created_branches.count(),
                'total_cashiers': User.objects.filter(role='cashier').count(),
                'total_supervisors': User.objects.filter(role='supervisor').count(),
                'total_accountants': User.objects.filter(role='accountant').count(),
                'active_cashiers': User.objects.filter(role='cashier', is_active=True).count(),
            }
        elif user.is_supervisor:
            branches = user.managed_branches.all()
            stats = {
                'managed_branches': branches.count(),
                'total_cashiers': User.objects.filter(role='cashier', branch__in=branches).count(),
                'active_cashiers': User.objects.filter(role='cashier', branch__in=branches, is_active=True).count(),
            }
        elif user.is_cashier and user.branch:
            from transactions.models import Transaction
            from django.utils import timezone
            today = timezone.now().date()
            stats = {
                'branch_name': user.branch.name,
                'today_transactions': Transaction.objects.filter(
                    cashier=user, created_at__date=today
                ).count(),
            }

        return Response(stats)
