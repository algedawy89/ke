"""
Transactions Views
"""
from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Sum, Count, Q

from .models import Transaction, TransactionLog
from .serializers import (
    TransactionSerializer, TransactionCreateSerializer,
    TransactionUpdateSerializer, TransactionDeleteSerializer
)
from accounts.permissions import (
    IsManager, IsManagerOrAccountant, IsCashier
)


class TransactionListView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'wallet', 'branch', 'cashier', 'shift_session', 'is_offline']
    search_fields = ['transaction_id', 'payment_reference', 'notes']
    ordering_fields = ['created_at', 'amount', 'payment_time']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        queryset = Transaction.objects.filter(is_deleted=False)

        if user.is_manager:
            return queryset
        elif user.is_supervisor:
            return queryset.filter(branch__manager=user)
        elif user.is_accountant:
            return queryset
        elif user.is_cashier:
            return queryset.filter(cashier=user)
        return queryset.none()


class TransactionDetailView(generics.RetrieveAPIView):
    queryset = Transaction.objects.filter(is_deleted=False)
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]


class TransactionCreateView(generics.CreateAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionCreateSerializer
    permission_classes = [IsCashier]

    def perform_create(self, serializer):
        serializer.save()


class TransactionUpdateView(generics.UpdateAPIView):
    queryset = Transaction.objects.filter(is_deleted=False)
    serializer_class = TransactionUpdateSerializer
    permission_classes = [IsCashier]

    def get_queryset(self):
        if self.request.user.is_cashier:
            return Transaction.objects.filter(cashier=self.request.user, is_deleted=False)
        return Transaction.objects.filter(is_deleted=False)


class TransactionDeleteView(generics.GenericAPIView):
    queryset = Transaction.objects.filter(is_deleted=False)
    permission_classes = [IsCashier]

    def post(self, request, pk=None):
        try:
            transaction = self.get_queryset().get(pk=pk)

            if request.user != transaction.cashier and not request.user.is_manager:
                return Response({'error': 'غير مصرح لك بحذف هذه العملية'}, status=status.HTTP_403_FORBIDDEN)

            if not transaction.is_deletable:
                return Response(
                    {'error': 'لا يمكن حذف هذه العملية (الوردية مغلقة)'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = TransactionDeleteSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            transaction.soft_delete(request.user, serializer.validated_data.get('reason', ''))
            return Response({'message': 'تم حذف العملية بنجاح'}, status=status.HTTP_200_OK)
        except Transaction.DoesNotExist:
            return Response({'error': 'العملية غير موجودة'}, status=status.HTTP_404_NOT_FOUND)


class TransactionRestoreView(generics.GenericAPIView):
    queryset = Transaction.objects.filter(is_deleted=True)
    permission_classes = [IsManager]

    def post(self, request, pk=None):
        try:
            transaction = self.get_queryset().get(pk=pk)
            transaction.restore(request.user)
            return Response({'message': 'تم استعادة العملية بنجاح'}, status=status.HTTP_200_OK)
        except Transaction.DoesNotExist:
            return Response({'error': 'العملية غير موجودة'}, status=status.HTTP_404_NOT_FOUND)


class TransactionReportView(generics.GenericAPIView):
    permission_classes = [IsManagerOrAccountant]

    def get(self, request):
        from django.utils.dateparse import parse_date

        branch_id = request.query_params.get('branch')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        wallet_id = request.query_params.get('wallet')

        queryset = Transaction.objects.filter(is_deleted=False, status='completed')

        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)
        if wallet_id:
            queryset = queryset.filter(wallet_id=wallet_id)
        if start_date:
            queryset = queryset.filter(created_at__date__gte=parse_date(start_date))
        if end_date:
            queryset = queryset.filter(created_at__date__lte=parse_date(end_date))

        summary = queryset.aggregate(
            total_amount=Sum('amount'),
            total_count=Count('id'),
            avg_amount=Sum('amount') / Count('id') if Count('id') > 0 else 0
        )

        by_wallet = queryset.values('wallet__name').annotate(
            total=Sum('amount'), count=Count('id')
        ).order_by('-total')

        by_day = queryset.extra(select={'day': 'date(created_at)'}).values('day').annotate(
            total=Sum('amount'), count=Count('id')
        ).order_by('day')

        return Response({
            'summary': summary,
            'by_wallet': by_wallet,
            'by_day': by_day,
            'transactions': TransactionSerializer(queryset[:50], many=True).data
        })
