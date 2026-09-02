"""
Transactions URLs
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.TransactionListView.as_view(), name='transaction-list'),
    path('create/', views.TransactionCreateView.as_view(), name='transaction-create'),
    path('<uuid:pk>/', views.TransactionDetailView.as_view(), name='transaction-detail'),
    path('<uuid:pk>/update/', views.TransactionUpdateView.as_view(), name='transaction-update'),
    path('<uuid:pk>/delete/', views.TransactionDeleteView.as_view(), name='transaction-delete'),
    path('<uuid:pk>/restore/', views.TransactionRestoreView.as_view(), name='transaction-restore'),
    path('reports/', views.TransactionReportView.as_view(), name='transaction-reports'),
]
