"""
Branches Views
"""
from rest_framework import generics, status, filters
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Branch
from .serializers import BranchSerializer, BranchCreateUpdateSerializer, BranchListSerializer
from accounts.permissions import IsManagerOrSupervisor, CanManageBranches


class BranchListView(generics.ListAPIView):
    """List all branches"""
    queryset = Branch.objects.all()
    serializer_class = BranchListSerializer
    permission_classes = [IsManagerOrSupervisor]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'manager']
    search_fields = ['name', 'address']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class BranchDetailView(generics.RetrieveAPIView):
    """Retrieve branch details"""
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = [IsManagerOrSupervisor]
    lookup_field = 'pk'


class BranchCreateView(generics.CreateAPIView):
    """Create new branch"""
    queryset = Branch.objects.all()
    serializer_class = BranchCreateUpdateSerializer
    permission_classes = [CanManageBranches]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class BranchUpdateView(generics.UpdateAPIView):
    """Update branch"""
    queryset = Branch.objects.all()
    serializer_class = BranchCreateUpdateSerializer
    permission_classes = [CanManageBranches]
    lookup_field = 'pk'


class BranchDeleteView(generics.DestroyAPIView):
    """Soft delete branch (deactivate)"""
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = [CanManageBranches]
    lookup_field = 'pk'

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


class BranchToggleActiveView(generics.GenericAPIView):
    """Toggle branch active status"""
    queryset = Branch.objects.all()
    permission_classes = [CanManageBranches]

    def post(self, request, pk=None):
        try:
            branch = self.get_queryset().get(pk=pk)
            branch.is_active = not branch.is_active
            branch.save()
            status_text = 'مفعل' if branch.is_active else 'معطل'
            return Response(
                {'message': f'تم {status_text} الفرع بنجاح', 'is_active': branch.is_active},
                status=status.HTTP_200_OK
            )
        except Branch.DoesNotExist:
            return Response({'error': 'الفرع غير موجود'}, status=status.HTTP_404_NOT_FOUND)
