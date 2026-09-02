"""
Dashboard URLs - All routes require superuser
"""
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Auth
    path('login/', views.DashboardLoginView.as_view(), name='login'),
    path('logout/', views.DashboardLogoutView.as_view(), name='logout'),
    
    # Main Dashboard
    path('', views.DashboardHomeView.as_view(), name='home'),

    # Branches
    path('branches/', views.BranchListView.as_view(), name='branch_list'),
    path('branches/add/', views.BranchCreateView.as_view(), name='branch_add'),
    path('branches/<uuid:pk>/', views.BranchDetailView.as_view(), name='branch_detail'),
    path('branches/<uuid:pk>/edit/', views.BranchUpdateView.as_view(), name='branch_edit'),
    path('branches/<uuid:pk>/delete/', views.BranchDeleteView.as_view(), name='branch_delete'),
    path('branches/<uuid:pk>/toggle/', views.BranchToggleView.as_view(), name='branch_toggle'),

    # Wallets
    path('wallets/', views.WalletListView.as_view(), name='wallet_list'),
    path('wallets/add/', views.WalletCreateView.as_view(), name='wallet_add'),
    path('wallets/<uuid:pk>/', views.WalletDetailView.as_view(), name='wallet_detail'),
    path('wallets/<uuid:pk>/edit/', views.WalletUpdateView.as_view(), name='wallet_edit'),
    path('wallets/<uuid:pk>/delete/', views.WalletDeleteView.as_view(), name='wallet_delete'),
    path('wallets/<uuid:pk>/toggle/', views.WalletToggleView.as_view(), name='wallet_toggle'),

    # Users
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/add/', views.UserCreateView.as_view(), name='user_add'),
    path('users/<uuid:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('users/<uuid:pk>/edit/', views.UserUpdateView.as_view(), name='user_edit'),
    path('users/<uuid:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),
    path('users/<uuid:pk>/toggle/', views.UserToggleView.as_view(), name='user_toggle'),
    path('users/<uuid:pk>/reset-password/', views.UserResetPasswordView.as_view(), name='user_reset_password'),

    # Cashiers
    path('cashiers/', views.CashierListView.as_view(), name='cashier_list'),
    path('cashiers/add/', views.CashierCreateView.as_view(), name='cashier_add'),
    path('cashiers/<uuid:pk>/edit/', views.CashierUpdateView.as_view(), name='cashier_edit'),
    path('cashiers/<uuid:pk>/toggle/', views.CashierToggleView.as_view(), name='cashier_toggle'),

    # Supervisors
    path('supervisors/', views.SupervisorListView.as_view(), name='supervisor_list'),
    path('supervisors/add/', views.SupervisorCreateView.as_view(), name='supervisor_add'),

    # Accountants
    path('accountants/', views.AccountantListView.as_view(), name='accountant_list'),
    path('accountants/add/', views.AccountantCreateView.as_view(), name='accountant_add'),

    # Shifts
    path('shifts/', views.ShiftListView.as_view(), name='shift_list'),
    path('shifts/add/', views.ShiftCreateView.as_view(), name='shift_add'),
    path('shifts/<uuid:pk>/edit/', views.ShiftUpdateView.as_view(), name='shift_edit'),
    path('shifts/<uuid:pk>/delete/', views.ShiftDeleteView.as_view(), name='shift_delete'),

    # Shift Sessions
    path('shift-sessions/', views.ShiftSessionListView.as_view(), name='shift_session_list'),
    path('shift-sessions/<uuid:pk>/reopen/', views.ShiftSessionReopenView.as_view(), name='shift_session_reopen'),

    # Transactions
    path('transactions/', views.TransactionListView.as_view(), name='transaction_list'),
    path('transactions/<uuid:pk>/', views.TransactionDetailView.as_view(), name='transaction_detail'),
    path('transactions/<uuid:pk>/restore/', views.TransactionRestoreView.as_view(), name='transaction_restore'),

    # Reports
    path('reports/', views.ReportsView.as_view(), name='reports'),
    path('reports/export/', views.ReportExportView.as_view(), name='report_export'),

    # Profile
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile_edit'),
    path('profile/change-password/', views.ChangePasswordView.as_view(), name='change_password'),

    # Settings
    path('settings/', views.SettingsView.as_view(), name='settings'),

    # Activity Logs
    path('activity-logs/', views.ActivityLogListView.as_view(), name='activity_logs'),

    # API Endpoints for AJAX
    path('api/stats/', views.DashboardStatsAPI.as_view(), name='api_stats'),
    path('api/chart-data/', views.ChartDataAPI.as_view(), name='api_chart_data'),
    path('api/wallet-search/', views.WalletSearchAPI.as_view(), name='api_wallet_search'),
]
