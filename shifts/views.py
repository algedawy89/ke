"""
Shifts Views
"""
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from .models import Shift, ShiftSession
from .serializers import (
    ShiftSerializer, ShiftCreateUpdateSerializer,
    ShiftSessionSerializer, ShiftSessionCreateSerializer,
    ShiftCloseSerializer, ShiftReopenSerializer
)
from accounts.permissions import IsManagerOrSupervisor, IsCashier


class ShiftListView(generics.ListAPIView):
    queryset = Shift.objects.all()
    serializer_class = ShiftSerializer
    permission_classes = [IsManagerOrSupervisor]


class ShiftCreateView(generics.CreateAPIView):
    queryset = Shift.objects.all()
    serializer_class = ShiftCreateUpdateSerializer
    permission_classes = [IsManagerOrSupervisor]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ShiftUpdateView(generics.UpdateAPIView):
    queryset = Shift.objects.all()
    serializer_class = ShiftCreateUpdateSerializer
    permission_classes = [IsManagerOrSupervisor]


class ShiftDeleteView(generics.DestroyAPIView):
    queryset = Shift.objects.all()
    serializer_class = ShiftSerializer
    permission_classes = [IsManagerOrSupervisor]


class ShiftSessionListView(generics.ListAPIView):
    serializer_class = ShiftSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_manager:
            return ShiftSession.objects.all()
        elif user.is_supervisor:
            return ShiftSession.objects.filter(branch__manager=user)
        elif user.is_cashier:
            return ShiftSession.objects.filter(cashier=user)
        return ShiftSession.objects.none()


class ShiftSessionCreateView(generics.CreateAPIView):
    queryset = ShiftSession.objects.all()
    serializer_class = ShiftSessionCreateSerializer
    permission_classes = [IsCashier]

    def perform_create(self, serializer):
        serializer.save()


class ShiftSessionCloseView(generics.GenericAPIView):
    queryset = ShiftSession.objects.all()
    permission_classes = [IsAuthenticated]

    def post(self, request, pk=None):
        try:
            session = self.get_queryset().get(pk=pk)
            if request.user != session.cashier and not request.user.is_supervisor and not request.user.is_manager:
                return Response({'error': 'غير مصرح لك بإغلاق هذه الوردية'}, status=status.HTTP_403_FORBIDDEN)

            serializer = ShiftCloseSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            session.close(request.user, serializer.validated_data.get('notes', ''))

            return Response(
                {'message': 'تم إغلاق الوردية بنجاح', 'session': ShiftSessionSerializer(session).data},
                status=status.HTTP_200_OK
            )
        except ShiftSession.DoesNotExist:
            return Response({'error': 'الوردية غير موجودة'}, status=status.HTTP_404_NOT_FOUND)


class ShiftSessionReopenView(generics.GenericAPIView):
    queryset = ShiftSession.objects.all()
    permission_classes = [IsManagerOrSupervisor]

    def post(self, request, pk=None):
        try:
            session = self.get_queryset().get(pk=pk)
            serializer = ShiftReopenSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            session.reopen(request.user, serializer.validated_data.get('reason', ''))

            return Response(
                {'message': 'تم إعادة فتح الوردية بنجاح', 'session': ShiftSessionSerializer(session).data},
                status=status.HTTP_200_OK
            )
        except ShiftSession.DoesNotExist:
            return Response({'error': 'الوردية غير موجودة'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_shift(request):
    if not request.user.is_cashier:
        return Response({'error': 'هذا المستخدم ليس كاشير'}, status=status.HTTP_400_BAD_REQUEST)

    now = timezone.now().time()
    shifts = Shift.objects.filter(branch=request.user.branch, is_active=True)

    active_shift = None
    for shift in shifts:
        if shift.is_currently_active:
            active_shift = shift
            break

    if not active_shift:
        return Response({'active_shift': None, 'message': 'لا توجد وردية نشطة حالياً'})

    open_session = ShiftSession.objects.filter(
        shift=active_shift, cashier=request.user, status__in=['open', 'reopened']
    ).first()

    return Response({
        'active_shift': ShiftSerializer(active_shift).data,
        'open_session': ShiftSessionSerializer(open_session).data if open_session else None
    })
