"""
Wallets Views
"""
from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from .models import Wallet
from .serializers import (
    WalletSerializer, WalletCreateUpdateSerializer,
    WalletListSerializer, WalletSearchSerializer
)
from accounts.permissions import IsManagerOrSupervisor


class WalletListView(generics.ListAPIView):
    """List all wallets"""
    queryset = Wallet.objects.all()
    serializer_class = WalletListSerializer
    permission_classes = [IsManagerOrSupervisor]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'branch']
    search_fields = ['name', 'name_en', 'wallet_code', 'keywords']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        user = self.request.user
        if user.is_manager:
            return Wallet.objects.all()
        elif user.is_supervisor:
            return Wallet.objects.filter(branch__manager=user)
        return Wallet.objects.none()


class WalletDetailView(generics.RetrieveAPIView):
    """Retrieve wallet details"""
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer
    permission_classes = [IsManagerOrSupervisor]
    lookup_field = 'pk'


class WalletCreateView(generics.CreateAPIView):
    """Create new wallet"""
    queryset = Wallet.objects.all()
    serializer_class = WalletCreateUpdateSerializer
    permission_classes = [IsManagerOrSupervisor]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class WalletUpdateView(generics.UpdateAPIView):
    """Update wallet"""
    queryset = Wallet.objects.all()
    serializer_class = WalletCreateUpdateSerializer
    permission_classes = [IsManagerOrSupervisor]
    lookup_field = 'pk'


class WalletDeleteView(generics.DestroyAPIView):
    """Soft delete wallet (deactivate)"""
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer
    permission_classes = [IsManagerOrSupervisor]
    lookup_field = 'pk'

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


class WalletToggleActiveView(generics.GenericAPIView):
    """Toggle wallet active status"""
    queryset = Wallet.objects.all()
    permission_classes = [IsManagerOrSupervisor]

    def post(self, request, pk=None):
        try:
            wallet = self.get_queryset().get(pk=pk)
            wallet.is_active = not wallet.is_active
            wallet.save()
            status_text = 'مفعلة' if wallet.is_active else 'معطلة'
            return Response(
                {'message': f'تم {status_text} المحفظة بنجاح', 'is_active': wallet.is_active},
                status=status.HTTP_200_OK
            )
        except Wallet.DoesNotExist:
            return Response({'error': 'المحفظة غير موجودة'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsManagerOrSupervisor])
def wallet_search(request):
    """Search wallets by keywords"""
    serializer = WalletSearchSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    query = serializer.validated_data['query']
    branch_id = serializer.validated_data.get('branch')

    wallets = Wallet.objects.filter(is_active=True)

    if branch_id:
        wallets = wallets.filter(branch_id=branch_id)

    # Search in name, name_en, wallet_code, and keywords
    wallets = wallets.filter(
        Q(name__icontains=query) |
        Q(name_en__icontains=query) |
        Q(wallet_code__icontains=query) |
        Q(keywords__icontains=query)
    )

    result_serializer = WalletListSerializer(wallets, many=True)
    return Response(result_serializer.data)


@api_view(['GET'])
@permission_classes([IsManagerOrSupervisor])
def wallet_by_branch(request, branch_id):
    """Get wallets by branch"""
    wallets = Wallet.objects.filter(branch_id=branch_id, is_active=True)
    serializer = WalletListSerializer(wallets, many=True)
    return Response(serializer.data)
