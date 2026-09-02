"""
Wallets URLs
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.WalletListView.as_view(), name='wallet-list'),
    path('create/', views.WalletCreateView.as_view(), name='wallet-create'),
    path('search/', views.wallet_search, name='wallet-search'),
    path('by-branch/<uuid:branch_id>/', views.wallet_by_branch, name='wallet-by-branch'),
    path('<uuid:pk>/', views.WalletDetailView.as_view(), name='wallet-detail'),
    path('<uuid:pk>/update/', views.WalletUpdateView.as_view(), name='wallet-update'),
    path('<uuid:pk>/delete/', views.WalletDeleteView.as_view(), name='wallet-delete'),
    path('<uuid:pk>/toggle-active/', views.WalletToggleActiveView.as_view(), name='wallet-toggle-active'),
]
