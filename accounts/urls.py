"""
Accounts URLs
"""
from django.urls import path
from . import views

urlpatterns = [
    # Users
    path('users/', views.UserListView.as_view(), name='user-list'),
    path('users/create/', views.UserCreateView.as_view(), name='user-create'),
    path('users/<uuid:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    path('users/<uuid:pk>/update/', views.UserUpdateView.as_view(), name='user-update'),
    path('users/<uuid:pk>/delete/', views.UserDeleteView.as_view(), name='user-delete'),

    # Cashiers
    path('cashiers/', views.CashierListView.as_view(), name='cashier-list'),
    path('cashiers/create/', views.CashierCreateView.as_view(), name='cashier-create'),
    path('cashiers/<uuid:pk>/update/', views.CashierUpdateView.as_view(), name='cashier-update'),
    path('cashiers/<uuid:pk>/toggle-active/', views.CashierToggleActiveView.as_view(), name='cashier-toggle-active'),

    # Profile & Auth
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('dashboard-stats/', views.DashboardStatsView.as_view(), name='dashboard-stats'),
]
