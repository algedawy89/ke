"""
Dashboard Views - All views require superuser
"""
import json
from datetime import datetime, timedelta
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Sum, Count, Q, Avg
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
)
from django.core.paginator import Paginator

from accounts.models import UserActivityLog
from branches.models import Branch
from wallets.models import Wallet
from shifts.models import Shift, ShiftSession
from transactions.models import Transaction, TransactionLog

User = get_user_model()


# ==================== MIXINS ====================

class SuperuserRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure only superusers can access"""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_superuser

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect('dashboard:login')
        messages.error(self.request, 'ليس لديك صلاحية الوصول إلى هذه الصفحة. يجب أن تكون مديراً.')
        return redirect('/')


class LogActivityMixin:
    """Mixin to log user activities"""
    def log_activity(self, action, entity_type, entity_id='', description=''):
        UserActivityLog.objects.create(
            user=self.request.user,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            description=description,
            ip_address=self.get_client_ip()
        )

    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return self.request.META.get('REMOTE_ADDR')


# ==================== DASHBOARD HOME ====================

class DashboardHomeView(SuperuserRequiredMixin, LogActivityMixin, TemplateView):
    template_name = 'dashboard/home_tailwind.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()

        # Statistics
        context['total_branches'] = Branch.objects.count()
        context['active_branches'] = Branch.objects.filter(is_active=True).count()
        context['total_wallets'] = Wallet.objects.count()
        context['active_wallets'] = Wallet.objects.filter(is_active=True).count()

        context['total_users'] = User.objects.count()
        context['total_cashiers'] = User.objects.filter(role='cashier').count()
        context['active_cashiers'] = User.objects.filter(role='cashier', is_active=True).count()
        context['total_supervisors'] = User.objects.filter(role='supervisor').count()
        context['total_accountants'] = User.objects.filter(role='accountant').count()

        # Today's transactions
        today_transactions = Transaction.objects.filter(
            is_deleted=False,
            created_at__date=today
        )
        context['today_transactions_count'] = today_transactions.count()
        context['today_total_amount'] = today_transactions.aggregate(
            total=Sum('amount')
        )['total'] or 0

        # This month
        month_start = today.replace(day=1)
        month_transactions = Transaction.objects.filter(
            is_deleted=False,
            created_at__date__gte=month_start
        )
        context['month_transactions_count'] = month_transactions.count()
        context['month_total_amount'] = month_transactions.aggregate(
            total=Sum('amount')
        )['total'] or 0

        # Recent transactions
        context['recent_transactions'] = Transaction.objects.filter(
            is_deleted=False
        ).select_related('wallet', 'cashier', 'branch').order_by('-created_at')[:10]

        # Recent activity logs
        context['recent_activities'] = UserActivityLog.objects.select_related(
            'user'
        ).order_by('-timestamp')[:10]

        # Open shift sessions
        context['open_sessions'] = ShiftSession.objects.filter(
            status__in=['open', 'reopened']
        ).select_related('shift', 'cashier', 'branch').order_by('-opened_at')[:10]

        # Top wallets
        context['top_wallets'] = Wallet.objects.annotate(
            total_amount=Sum('transactions__amount', filter=Q(transactions__is_deleted=False))
        ).order_by('-total_amount')[:5]

        # Branch stats
        context['branch_stats'] = Branch.objects.annotate(
            trans_count=Count('transactions', filter=Q(transactions__is_deleted=False)),
            trans_total=Sum('transactions__amount', filter=Q(transactions__is_deleted=False))
        ).order_by('-trans_total')[:5]

        return context

    def get(self, request, *args, **kwargs):
        self.log_activity('view', 'dashboard', description='زيارة لوحة التحكم')
        return super().get(request, *args, **kwargs)


# ==================== BRANCHES ====================

class BranchListView(SuperuserRequiredMixin, LogActivityMixin, ListView):
    model = Branch
    template_name = 'dashboard/branches/list.html'
    context_object_name = 'branches'
    paginate_by = 20

    def get_queryset(self):
        queryset = Branch.objects.all().annotate(
            cashiers_count=Count('cashiers', filter=Q(cashiers__role='cashier')),
            wallets_count=Count('wallets'),
            trans_count=Count('transactions', filter=Q(transactions__is_deleted=False)),
            trans_total=Sum('transactions__amount', filter=Q(transactions__is_deleted=False))
        )

        # Search
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search) |
                Q(city__icontains=search) |
                Q(address__icontains=search)
            )

        # Filter by status
        status_filter = self.request.GET.get('status')
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['status_filter'] = self.request.GET.get('status', '')
        return context


class BranchDetailView(SuperuserRequiredMixin, LogActivityMixin, DetailView):
    model = Branch
    template_name = 'dashboard/branches/detail.html'
    context_object_name = 'branch'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        branch = self.object

        # Cashiers in this branch
        context['cashiers'] = User.objects.filter(
            branch=branch, role='cashier'
        ).order_by('-date_joined')

        # Wallets in this branch
        context['wallets'] = Wallet.objects.filter(branch=branch).order_by('-created_at')

        # Shifts in this branch
        context['shifts'] = Shift.objects.filter(branch=branch).order_by('start_time')

        # Recent transactions
        context['recent_transactions'] = Transaction.objects.filter(
            branch=branch, is_deleted=False
        ).select_related('wallet', 'cashier').order_by('-created_at')[:20]

        # Transaction stats
        today = timezone.now().date()
        context['today_count'] = Transaction.objects.filter(
            branch=branch, is_deleted=False, created_at__date=today
        ).count()
        context['today_total'] = Transaction.objects.filter(
            branch=branch, is_deleted=False, created_at__date=today
        ).aggregate(total=Sum('amount'))['total'] or 0

        # Monthly stats
        month_start = today.replace(day=1)
        context['month_count'] = Transaction.objects.filter(
            branch=branch, is_deleted=False, created_at__date__gte=month_start
        ).count()
        context['month_total'] = Transaction.objects.filter(
            branch=branch, is_deleted=False, created_at__date__gte=month_start
        ).aggregate(total=Sum('amount'))['total'] or 0

        return context


class BranchCreateView(SuperuserRequiredMixin, LogActivityMixin, CreateView):
    model = Branch
    template_name = 'dashboard/branches/form.html'
    fields = ['name', 'code', 'address', 'phone', 'email', 'city', 'region', 'manager', 'is_active']
    success_url = reverse_lazy('dashboard:branch_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f'تم إنشاء الفرع "{form.instance.name}" بنجاح')
        self.log_activity('create', 'branch', form.instance.id, f'إنشاء فرع: {form.instance.name}')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'إضافة فرع جديد'
        context['action'] = 'add'
        context['supervisors'] = User.objects.filter(role='supervisor', is_active=True)
        return context


class BranchUpdateView(SuperuserRequiredMixin, LogActivityMixin, UpdateView):
    model = Branch
    template_name = 'dashboard/branches/form.html'
    fields = ['name', 'code', 'address', 'phone', 'email', 'city', 'region', 'manager', 'is_active']
    success_url = reverse_lazy('dashboard:branch_list')

    def form_valid(self, form):
        messages.success(self.request, f'تم تحديث الفرع "{form.instance.name}" بنجاح')
        self.log_activity('update', 'branch', form.instance.id, f'تحديث فرع: {form.instance.name}')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'تعديل الفرع'
        context['action'] = 'edit'
        context['supervisors'] = User.objects.filter(role='supervisor', is_active=True)
        return context


class BranchDeleteView(SuperuserRequiredMixin, LogActivityMixin, View):
    def post(self, request, pk):
        branch = get_object_or_404(Branch, pk=pk)
        name = branch.name
        branch.delete()
        messages.success(request, f'تم حذف الفرع "{name}" بنجاح')
        self.log_activity('delete', 'branch', pk, f'حذف فرع: {name}')
        return redirect('dashboard:branch_list')


class BranchToggleView(SuperuserRequiredMixin, LogActivityMixin, View):
    def post(self, request, pk):
        branch = get_object_or_404(Branch, pk=pk)
        branch.is_active = not branch.is_active
        branch.save()
        status_text = 'تفعيل' if branch.is_active else 'تعطيل'
        messages.success(request, f'تم {status_text} الفرع "{branch.name}" بنجاح')
        self.log_activity('update', 'branch', branch.id, f'{status_text} فرع: {branch.name}')
        return redirect('dashboard:branch_list')


# ==================== WALLETS ====================

class WalletListView(SuperuserRequiredMixin, LogActivityMixin, ListView):
    model = Wallet
    template_name = 'dashboard/wallets/list.html'
    context_object_name = 'wallets'
    paginate_by = 20

    def get_queryset(self):
        queryset = Wallet.objects.all().select_related('branch').annotate(
            trans_count=Count('transactions', filter=Q(transactions__is_deleted=False)),
            trans_total=Sum('transactions__amount', filter=Q(transactions__is_deleted=False))
        )

        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(name_en__icontains=search) |
                Q(wallet_code__icontains=search) |
                Q(keywords__icontains=search) |
                Q(branch__name__icontains=search)
            )

        branch_filter = self.request.GET.get('branch')
        if branch_filter:
            queryset = queryset.filter(branch_id=branch_filter)

        status_filter = self.request.GET.get('status')
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['branch_filter'] = self.request.GET.get('branch', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['branches'] = Branch.objects.filter(is_active=True)
        return context


class WalletDetailView(SuperuserRequiredMixin, LogActivityMixin, DetailView):
    model = Wallet
    template_name = 'dashboard/wallets/detail.html'
    context_object_name = 'wallet'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        wallet = self.object

        context['transactions'] = Transaction.objects.filter(
            wallet=wallet, is_deleted=False
        ).select_related('cashier', 'branch').order_by('-created_at')[:50]

        today = timezone.now().date()
        context['today_count'] = Transaction.objects.filter(
            wallet=wallet, is_deleted=False, created_at__date=today
        ).count()
        context['today_total'] = Transaction.objects.filter(
            wallet=wallet, is_deleted=False, created_at__date=today
        ).aggregate(total=Sum('amount'))['total'] or 0

        return context


class WalletCreateView(SuperuserRequiredMixin, LogActivityMixin, CreateView):
    model = Wallet
    template_name = 'dashboard/wallets/form.html'
    fields = ['name', 'name_en', 'wallet_code', 'phone_number', 'logo', 'keywords', 'branch', 'is_active']
    success_url = reverse_lazy('dashboard:wallet_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f'تم إنشاء المحفظة "{form.instance.name}" بنجاح')
        self.log_activity('create', 'wallet', form.instance.id, f'إنشاء محفظة: {form.instance.name}')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'إضافة محفظة جديدة'
        context['action'] = 'add'
        context['branches'] = Branch.objects.filter(is_active=True)
        return context


class WalletUpdateView(SuperuserRequiredMixin, LogActivityMixin, UpdateView):
    model = Wallet
    template_name = 'dashboard/wallets/form.html'
    fields = ['name', 'name_en', 'wallet_code', 'phone_number', 'logo', 'keywords', 'branch', 'is_active']
    success_url = reverse_lazy('dashboard:wallet_list')

    def form_valid(self, form):
        messages.success(self.request, f'تم تحديث المحفظة "{form.instance.name}" بنجاح')
        self.log_activity('update', 'wallet', form.instance.id, f'تحديث محفظة: {form.instance.name}')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'تعديل المحفظة'
        context['action'] = 'edit'
        context['branches'] = Branch.objects.filter(is_active=True)
        return context


class WalletDeleteView(SuperuserRequiredMixin, LogActivityMixin, View):
    def post(self, request, pk):
        wallet = get_object_or_404(Wallet, pk=pk)
        name = wallet.name
        wallet.delete()
        messages.success(request, f'تم حذف المحفظة "{name}" بنجاح')
        self.log_activity('delete', 'wallet', pk, f'حذف محفظة: {name}')
        return redirect('dashboard:wallet_list')


class WalletToggleView(SuperuserRequiredMixin, LogActivityMixin, View):
    def post(self, request, pk):
        wallet = get_object_or_404(Wallet, pk=pk)
        wallet.is_active = not wallet.is_active
        wallet.save()
        status_text = 'تفعيل' if wallet.is_active else 'تعطيل'
        messages.success(request, f'تم {status_text} المحفظة "{wallet.name}" بنجاح')
        self.log_activity('update', 'wallet', wallet.id, f'{status_text} محفظة: {wallet.name}')
        return redirect('dashboard:wallet_list')


# ==================== USERS ====================

class UserListView(SuperuserRequiredMixin, LogActivityMixin, ListView):
    model = User
    template_name = 'dashboard/users/list.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        queryset = User.objects.all().select_related('branch')

        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search) |
                Q(username__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search)
            )

        role_filter = self.request.GET.get('role')
        if role_filter:
            queryset = queryset.filter(role=role_filter)

        status_filter = self.request.GET.get('status')
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)

        branch_filter = self.request.GET.get('branch')
        if branch_filter:
            queryset = queryset.filter(branch_id=branch_filter)

        return queryset.order_by('-date_joined')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['role_filter'] = self.request.GET.get('role', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['branch_filter'] = self.request.GET.get('branch', '')
        context['branches'] = Branch.objects.filter(is_active=True)
        context['roles'] = User.Role.choices
        return context


class UserDetailView(SuperuserRequiredMixin, LogActivityMixin, DetailView):
    model = User
    template_name = 'dashboard/users/detail.html'
    context_object_name = 'user_obj'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object

        if user.role == 'cashier':
            context['transactions'] = Transaction.objects.filter(
                cashier=user, is_deleted=False
            ).select_related('wallet', 'branch').order_by('-created_at')[:30]

            context['shift_sessions'] = ShiftSession.objects.filter(
                cashier=user
            ).select_related('shift', 'branch').order_by('-opened_at')[:20]

        context['activity_logs'] = UserActivityLog.objects.filter(
            user=user
        ).order_by('-timestamp')[:30]

        return context


class UserCreateView(SuperuserRequiredMixin, LogActivityMixin, CreateView):
    model = User
    template_name = 'dashboard/users/form.html'
    fields = ['username', 'full_name', 'email', 'phone', 'role', 'branch', 
              'profile_image', 'id_card_front', 'id_card_back', 'is_active']
    success_url = reverse_lazy('dashboard:user_list')

    def form_valid(self, form):
        # Set default password
        if form.instance.phone:
            pw=form.isinstance.phone
        else:
            pw='12345678'
        form.instance.set_password(pw)
        form.instance.created_by = self.request.user
        messages.success(self.request, f'تم إنشاء المستخدم "{form.instance.full_name}" بنجاح. كلمة المرور الافتراضية: 12345678')
        self.log_activity('create', 'user', form.instance.id, f'إنشاء مستخدم: {form.instance.full_name} ({form.instance.get_role_display()})')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'إضافة مستخدم جديد'
        context['action'] = 'add'
        context['branches'] = Branch.objects.filter(is_active=True)
        context['roles'] = [
            ('manager', 'مدير'),
            ('supervisor', 'مشرف'),
            ('accountant', 'محاسب'),
            ('cashier', 'كاشير'),
        ]
        return context


class UserUpdateView(SuperuserRequiredMixin, LogActivityMixin, UpdateView):
    model = User
    template_name = 'dashboard/users/form.html'
    fields = ['username', 'full_name', 'email', 'phone', 'role', 'branch',
              'profile_image', 'id_card_front', 'id_card_back', 'is_active']
    success_url = reverse_lazy('dashboard:user_list')

    def form_valid(self, form):
        messages.success(self.request, f'تم تحديث المستخدم "{form.instance.full_name}" بنجاح')
        self.log_activity('update', 'user', form.instance.id, f'تحديث مستخدم: {form.instance.full_name}')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'تعديل المستخدم'
        context['action'] = 'edit'
        context['branches'] = Branch.objects.filter(is_active=True)
        context['roles'] = [
            ('manager', 'مدير'),
            ('supervisor', 'مشرف'),
            ('accountant', 'محاسب'),
            ('cashier', 'كاشير'),
        ]
        return context


class UserDeleteView(SuperuserRequiredMixin, LogActivityMixin, View):
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if user == request.user:
            messages.error(request, 'لا يمكنك حذف حسابك الخاص')
            return redirect('dashboard:user_list')
        name = user.full_name
        user.delete()
        messages.success(request, f'تم حذف المستخدم "{name}" بنجاح')
        self.log_activity('delete', 'user', pk, f'حذف مستخدم: {name}')
        return redirect('dashboard:user_list')


class UserToggleView(SuperuserRequiredMixin, LogActivityMixin, View):
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if user == request.user:
            messages.error(request, 'لا يمكنك تعطيل حسابك الخاص')
            return redirect('dashboard:user_list')
        user.is_active = not user.is_active
        user.save()
        status_text = 'تفعيل' if user.is_active else 'تعطيل'
        messages.success(request, f'تم {status_text} المستخدم "{user.full_name}" بنجاح')
        self.log_activity('update', 'user', user.id, f'{status_text} مستخدم: {user.full_name}')
        return redirect('dashboard:user_list')


class UserResetPasswordView(SuperuserRequiredMixin, LogActivityMixin, View):
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user.set_password('12345678')
        user.save()
        messages.success(request, f'تم إعادة تعيين كلمة المرور للمستخدم "{user.full_name}" إلى: 12345678')
        self.log_activity('update', 'user', user.id, f'إعادة تعيين كلمة مرور: {user.full_name}')
        return redirect('dashboard:user_list')


# ==================== CASHIERS ====================

class CashierListView(SuperuserRequiredMixin, LogActivityMixin, ListView):
    model = User
    template_name = 'dashboard/users/cashier_list.html'
    context_object_name = 'cashiers'
    paginate_by = 20

    def get_queryset(self):
        queryset = User.objects.filter(role='cashier').select_related('branch')

        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search) |
                Q(username__icontains=search) |
                Q(phone__icontains=search)
            )

        branch_filter = self.request.GET.get('branch')
        if branch_filter:
            queryset = queryset.filter(branch_id=branch_filter)

        status_filter = self.request.GET.get('status')
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)

        return queryset.order_by('-date_joined')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['branch_filter'] = self.request.GET.get('branch', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['branches'] = Branch.objects.filter(is_active=True)
        return context


class CashierCreateView(SuperuserRequiredMixin, LogActivityMixin, CreateView):
    model = User
    template_name = 'dashboard/users/cashier_form.html'
    fields = ['username', 'full_name', 'phone', 'branch',
              'profile_image', 'id_card_front', 'id_card_back', 'is_active']
    success_url = reverse_lazy('dashboard:cashier_list')

    def form_valid(self, form):
        form.instance.role = 'cashier'
        form.instance.set_password('12345678')
        form.instance.created_by = self.request.user
        messages.success(self.request, f'تم إنشاء الكاشير "{form.instance.full_name}" بنجاح')
        self.log_activity('create', 'cashier', form.instance.id, f'إنشاء كاشير: {form.instance.full_name}')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'إضافة كاشير جديد'
        context['action'] = 'add'
        context['branches'] = Branch.objects.filter(is_active=True)
        return context


class CashierUpdateView(SuperuserRequiredMixin, LogActivityMixin, UpdateView):
    model = User
    template_name = 'dashboard/users/cashier_form.html'
    fields = ['username', 'full_name', 'phone', 'branch',
              'profile_image', 'id_card_front', 'id_card_back', 'is_active']
    success_url = reverse_lazy('dashboard:cashier_list')

    def get_queryset(self):
        return User.objects.filter(role='cashier')

    def form_valid(self, form):
        messages.success(self.request, f'تم تحديث الكاشير "{form.instance.full_name}" بنجاح')
        self.log_activity('update', 'cashier', form.instance.id, f'تحديث كاشير: {form.instance.full_name}')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'تعديل الكاشير'
        context['action'] = 'edit'
        context['branches'] = Branch.objects.filter(is_active=True)
        return context


class CashierToggleView(SuperuserRequiredMixin, LogActivityMixin, View):
    def post(self, request, pk):
        cashier = get_object_or_404(User, pk=pk, role='cashier')
        cashier.is_active = not cashier.is_active
        cashier.save()
        status_text = 'تفعيل' if cashier.is_active else 'تعطيل'
        messages.success(request, f'تم {status_text} الكاشير "{cashier.full_name}" بنجاح')
        self.log_activity('update', 'cashier', cashier.id, f'{status_text} كاشير: {cashier.full_name}')
        return redirect('dashboard:cashier_list')


# ==================== SUPERVISORS ====================

class SupervisorListView(SuperuserRequiredMixin, LogActivityMixin, ListView):
    model = User
    template_name = 'dashboard/users/supervisor_list.html'
    context_object_name = 'supervisors'
    paginate_by = 20

    def get_queryset(self):
        queryset = User.objects.filter(role='supervisor')
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search) |
                Q(username__icontains=search) |
                Q(phone__icontains=search)
            )
        return queryset.order_by('-date_joined')


class SupervisorCreateView(SuperuserRequiredMixin, LogActivityMixin, CreateView):
    model = User
    template_name = 'dashboard/users/supervisor_form.html'
    fields = ['username', 'full_name', 'email', 'phone', 'is_active']
    success_url = reverse_lazy('dashboard:supervisor_list')

    def form_valid(self, form):
        form.instance.role = 'supervisor'
        form.instance.set_password('12345678')
        form.instance.created_by = self.request.user
        messages.success(self.request, f'تم إنشاء المشرف "{form.instance.full_name}" بنجاح')
        self.log_activity('create', 'supervisor', form.instance.id, f'إنشاء مشرف: {form.instance.full_name}')
        return super().form_valid(form)


# ==================== ACCOUNTANTS ====================

class AccountantListView(SuperuserRequiredMixin, LogActivityMixin, ListView):
    model = User
    template_name = 'dashboard/users/accountant_list.html'
    context_object_name = 'accountants'
    paginate_by = 20

    def get_queryset(self):
        queryset = User.objects.filter(role='accountant')
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search) |
                Q(username__icontains=search) |
                Q(phone__icontains=search)
            )
        return queryset.order_by('-date_joined')


class AccountantCreateView(SuperuserRequiredMixin, LogActivityMixin, CreateView):
    model = User
    template_name = 'dashboard/users/accountant_form.html'
    fields = ['username', 'full_name', 'email', 'phone', 'is_active']
    success_url = reverse_lazy('dashboard:accountant_list')

    def form_valid(self, form):
        form.instance.role = 'accountant'
        form.instance.set_password('12345678')
        form.instance.created_by = self.request.user
        messages.success(self.request, f'تم إنشاء المحاسب "{form.instance.full_name}" بنجاح')
        self.log_activity('create', 'accountant', form.instance.id, f'إنشاء محاسب: {form.instance.full_name}')
        return super().form_valid(form)


# ==================== SHIFTS ====================

class ShiftListView(SuperuserRequiredMixin, LogActivityMixin, ListView):
    model = Shift
    template_name = 'dashboard/shifts/list.html'
    context_object_name = 'shifts'
    paginate_by = 20

    def get_queryset(self):
        queryset = Shift.objects.all().select_related('branch')

        branch_filter = self.request.GET.get('branch')
        if branch_filter:
            queryset = queryset.filter(branch_id=branch_filter)

        return queryset.order_by('branch__name', 'start_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['branch_filter'] = self.request.GET.get('branch', '')
        context['branches'] = Branch.objects.filter(is_active=True)
        return context


class ShiftCreateView(SuperuserRequiredMixin, LogActivityMixin, CreateView):
    model = Shift
    template_name = 'dashboard/shifts/form.html'
    fields = ['name', 'shift_type', 'start_time', 'end_time', 'branch', 'is_active']
    success_url = reverse_lazy('dashboard:shift_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f'تم إنشاء الوردية "{form.instance.name}" بنجاح')
        self.log_activity('create', 'shift', form.instance.id, f'إنشاء وردية: {form.instance.name}')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'إضافة وردية جديدة'
        context['action'] = 'add'
        context['branches'] = Branch.objects.filter(is_active=True)
        context['shift_types'] = Shift.ShiftType.choices
        return context


class ShiftUpdateView(SuperuserRequiredMixin, LogActivityMixin, UpdateView):
    model = Shift
    template_name = 'dashboard/shifts/form.html'
    fields = ['name', 'shift_type', 'start_time', 'end_time', 'branch', 'is_active']
    success_url = reverse_lazy('dashboard:shift_list')

    def form_valid(self, form):
        messages.success(self.request, f'تم تحديث الوردية "{form.instance.name}" بنجاح')
        self.log_activity('update', 'shift', form.instance.id, f'تحديث وردية: {form.instance.name}')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'تعديل الوردية'
        context['action'] = 'edit'
        context['branches'] = Branch.objects.filter(is_active=True)
        context['shift_types'] = Shift.ShiftType.choices
        return context


class ShiftDeleteView(SuperuserRequiredMixin, LogActivityMixin, View):
    def post(self, request, pk):
        shift = get_object_or_404(Shift, pk=pk)
        name = shift.name
        shift.delete()
        messages.success(request, f'تم حذف الوردية "{name}" بنجاح')
        self.log_activity('delete', 'shift', pk, f'حذف وردية: {name}')
        return redirect('dashboard:shift_list')


# ==================== SHIFT SESSIONS ====================

class ShiftSessionListView(SuperuserRequiredMixin, LogActivityMixin, ListView):
    model = ShiftSession
    template_name = 'dashboard/shifts/session_list.html'
    context_object_name = 'sessions'
    paginate_by = 20

    def get_queryset(self):
        queryset = ShiftSession.objects.all().select_related(
            'shift', 'cashier', 'branch', 'closed_by', 'reopened_by'
        )

        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        branch_filter = self.request.GET.get('branch')
        if branch_filter:
            queryset = queryset.filter(branch_id=branch_filter)

        return queryset.order_by('-opened_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_filter'] = self.request.GET.get('status', '')
        context['branch_filter'] = self.request.GET.get('branch', '')
        context['branches'] = Branch.objects.filter(is_active=True)
        context['statuses'] = ShiftSession.Status.choices
        return context


class ShiftSessionReopenView(SuperuserRequiredMixin, LogActivityMixin, View):
    def post(self, request, pk):
        session = get_object_or_404(ShiftSession, pk=pk)
        reason = request.POST.get('reason', '')
        session.reopen(request.user, reason)
        messages.success(request, f'تم إعادة فتح الوردية بنجاح')
        self.log_activity('update', 'shift_session', session.id, f'إعادة فتح وردية: {session.shift.name}')
        return redirect('dashboard:shift_session_list')


# ==================== TRANSACTIONS ====================

class TransactionListView(SuperuserRequiredMixin, LogActivityMixin, ListView):
    model = Transaction
    template_name = 'dashboard/transactions/list.html'
    context_object_name = 'transactions'
    paginate_by = 30

    def get_queryset(self):
        queryset = Transaction.objects.filter(is_deleted=False).select_related(
            'wallet', 'cashier', 'branch', 'shift_session'
        )

        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(transaction_id__icontains=search) |
                Q(payment_reference__icontains=search) |
                Q(notes__icontains=search)
            )

        branch_filter = self.request.GET.get('branch')
        if branch_filter:
            queryset = queryset.filter(branch_id=branch_filter)

        wallet_filter = self.request.GET.get('wallet')
        if wallet_filter:
            queryset = queryset.filter(wallet_id=wallet_filter)

        cashier_filter = self.request.GET.get('cashier')
        if cashier_filter:
            queryset = queryset.filter(cashier_id=cashier_filter)

        date_from = self.request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)

        date_to = self.request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['branch_filter'] = self.request.GET.get('branch', '')
        context['wallet_filter'] = self.request.GET.get('wallet', '')
        context['cashier_filter'] = self.request.GET.get('cashier', '')
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')

        context['branches'] = Branch.objects.filter(is_active=True)
        context['wallets'] = Wallet.objects.filter(is_active=True)
        context['cashiers'] = User.objects.filter(role='cashier', is_active=True)

        # Summary
        context['total_count'] = self.get_queryset().count()
        context['total_amount'] = self.get_queryset().aggregate(
            total=Sum('amount')
        )['total'] or 0

        return context


class TransactionDetailView(SuperuserRequiredMixin, LogActivityMixin, DetailView):
    model = Transaction
    template_name = 'dashboard/transactions/detail.html'
    context_object_name = 'transaction'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['logs'] = TransactionLog.objects.filter(
            transaction=self.object
        ).select_related('user').order_by('-timestamp')[:20]
        return context


class TransactionRestoreView(SuperuserRequiredMixin, LogActivityMixin, View):
    def post(self, request, pk):
        transaction = get_object_or_404(Transaction, pk=pk, is_deleted=True)
        transaction.restore(request.user)
        messages.success(request, f'تم استعادة العملية بنجاح')
        self.log_activity('restore', 'transaction', transaction.id, f'استعادة عملية: {transaction.transaction_id}')
        return redirect('dashboard:transaction_list')


# ==================== REPORTS ====================

class ReportsView(SuperuserRequiredMixin, LogActivityMixin, TemplateView):
    template_name = 'dashboard/reports/reports.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        branch_id = self.request.GET.get('branch')
        wallet_id = self.request.GET.get('wallet')

        queryset = Transaction.objects.filter(is_deleted=False, status='completed')

        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)
        if wallet_id:
            queryset = queryset.filter(wallet_id=wallet_id)

        # Summary
        summary = queryset.aggregate(
            total_amount=Sum('amount'),
            total_count=Count('id'),
            avg_amount=Avg('amount')
        )
        context['summary'] = summary
        context['total_amount'] = summary['total_amount'] or 0
        context['total_count'] = summary['total_count'] or 0
        context['avg_amount'] = summary['avg_amount'] or 0

        # By wallet
        context['by_wallet'] = queryset.values('wallet__name').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')

        # By branch
        context['by_branch'] = queryset.values('branch__name').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')

        # By cashier
        context['by_cashier'] = queryset.values('cashier__full_name').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')[:10]

        # By day (last 30 days)
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        context['by_day'] = queryset.filter(
            created_at__date__gte=thirty_days_ago
        ).extra(select={'day': 'date(created_at)'}).values('day').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('day')

        # Filters
        context['date_from'] = date_from or ''
        context['date_to'] = date_to or ''
        context['branch_filter'] = branch_id or ''
        context['wallet_filter'] = wallet_id or ''
        context['branches'] = Branch.objects.filter(is_active=True)
        context['wallets'] = Wallet.objects.filter(is_active=True)

        return context


class ReportExportView(SuperuserRequiredMixin, View):
    def get(self, request):
        import csv
        from io import StringIO

        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        branch_id = request.GET.get('branch')

        queryset = Transaction.objects.filter(is_deleted=False).select_related(
            'wallet', 'cashier', 'branch'
        )

        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'رقم العملية', 'المبلغ', 'المحفظة', 'الفرع', 'الكاشير',
            'رقم مرجعي', 'الوقت', 'الحالة'
        ])

        for t in queryset:
            writer.writerow([
                t.transaction_id,
                t.amount,
                t.wallet.name if t.wallet else '',
                t.branch.name if t.branch else '',
                t.cashier.full_name if t.cashier else '',
                t.payment_reference,
                t.created_at.strftime('%Y-%m-%d %H:%M'),
                t.get_status_display()
            ])

        response = HttpResponse(output.getvalue(), content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="transactions_report.csv"'
        return response


# ==================== PROFILE ====================

class ProfileView(SuperuserRequiredMixin, TemplateView):
    template_name = 'dashboard/profile/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_obj'] = self.request.user
        context['activity_logs'] = UserActivityLog.objects.filter(
            user=self.request.user
        ).order_by('-timestamp')[:20]
        return context


class ProfileUpdateView(SuperuserRequiredMixin, UpdateView):
    model = User
    template_name = 'dashboard/profile/edit.html'
    fields = ['full_name', 'email', 'phone', 'profile_image']
    success_url = reverse_lazy('dashboard:profile')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'تم تحديث الملف الشخصي بنجاح')
        return super().form_valid(form)


class ChangePasswordView(SuperuserRequiredMixin, View):
    def get(self, request):
        return render(request, 'dashboard/profile/change_password.html')

    def post(self, request):
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        new_password_confirm = request.POST.get('new_password_confirm')

        if not request.user.check_password(old_password):
            messages.error(request, 'كلمة المرور الحالية غير صحيحة')
            return redirect('dashboard:change_password')

        if new_password != new_password_confirm:
            messages.error(request, 'كلمات المرور الجديدة غير متطابقة')
            return redirect('dashboard:change_password')

        if len(new_password) < 8:
            messages.error(request, 'يجب أن تكون كلمة المرور 8 أحرف على الأقل')
            return redirect('dashboard:change_password')

        request.user.set_password(new_password)
        request.user.save()
        messages.success(request, 'تم تغيير كلمة المرور بنجاح. يرجى تسجيل الدخول مرة أخرى.')
        return redirect('dashboard:login')


# ==================== SETTINGS ====================

class SettingsView(SuperuserRequiredMixin, TemplateView):
    template_name = 'dashboard/settings/settings.html'


# ==================== ACTIVITY LOGS ====================

class ActivityLogListView(SuperuserRequiredMixin, ListView):
    model = UserActivityLog
    template_name = 'dashboard/activity_logs/list.html'
    context_object_name = 'logs'
    paginate_by = 50

    def get_queryset(self):
        queryset = UserActivityLog.objects.all().select_related('user')

        user_filter = self.request.GET.get('user')
        if user_filter:
            queryset = queryset.filter(user_id=user_filter)

        action_filter = self.request.GET.get('action')
        if action_filter:
            queryset = queryset.filter(action=action_filter)

        date_from = self.request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(timestamp__date__gte=date_from)

        date_to = self.request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(timestamp__date__lte=date_to)

        return queryset.order_by('-timestamp')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_filter'] = self.request.GET.get('user', '')
        context['action_filter'] = self.request.GET.get('action', '')
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')
        context['users'] = User.objects.filter(is_active=True)
        context['actions'] = UserActivityLog.ActionType.choices
        return context


# ==================== API ENDPOINTS (AJAX) ====================

class DashboardStatsAPI(SuperuserRequiredMixin, View):
    def get(self, request):
        today = timezone.now().date()

        data = {
            'total_branches': Branch.objects.count(),
            'active_branches': Branch.objects.filter(is_active=True).count(),
            'total_wallets': Wallet.objects.count(),
            'active_wallets': Wallet.objects.filter(is_active=True).count(),
            'total_users': User.objects.count(),
            'active_cashiers': User.objects.filter(role='cashier', is_active=True).count(),
            'today_transactions': Transaction.objects.filter(
                is_deleted=False, created_at__date=today
            ).count(),
            'today_amount': float(Transaction.objects.filter(
                is_deleted=False, created_at__date=today
            ).aggregate(total=Sum('amount'))['total'] or 0),
            'open_sessions': ShiftSession.objects.filter(
                status__in=['open', 'reopened']
            ).count(),
        }
        return JsonResponse(data)


class ChartDataAPI(SuperuserRequiredMixin, View):
    def get(self, request):
        chart_type = request.GET.get('type', 'daily')

        if chart_type == 'daily':
            # Last 7 days
            dates = []
            amounts = []
            counts = []
            for i in range(6, -1, -1):
                date = timezone.now().date() - timedelta(days=i)
                day_transactions = Transaction.objects.filter(
                    is_deleted=False,
                    created_at__date=date
                )
                dates.append(date.strftime('%Y-%m-%d'))
                amounts.append(float(day_transactions.aggregate(
                    total=Sum('amount')
                )['total'] or 0))
                counts.append(day_transactions.count())

            return JsonResponse({
                'labels': dates,
                'amounts': amounts,
                'counts': counts
            })

        elif chart_type == 'wallet':
            wallet_data = Wallet.objects.annotate(
                total=Sum('transactions__amount', filter=Q(transactions__is_deleted=False))
            ).filter(total__gt=0).order_by('-total')[:10]

            return JsonResponse({
                'labels': [w.name for w in wallet_data],
                'amounts': [float(w.total or 0) for w in wallet_data]
            })

        elif chart_type == 'branch':
            branch_data = Branch.objects.annotate(
                total=Sum('transactions__amount', filter=Q(transactions__is_deleted=False))
            ).filter(total__gt=0).order_by('-total')[:10]

            return JsonResponse({
                'labels': [b.name for b in branch_data],
                'amounts': [float(b.total or 0) for b in branch_data]
            })

        return JsonResponse({'error': 'Invalid chart type'})


class WalletSearchAPI(SuperuserRequiredMixin, View):
    def get(self, request):
        query = request.GET.get('q', '')
        branch_id = request.GET.get('branch')

        wallets = Wallet.objects.filter(is_active=True)

        if branch_id:
            wallets = wallets.filter(branch_id=branch_id)

        if query:
            wallets = wallets.filter(
                Q(name__icontains=query) |
                Q(name_en__icontains=query) |
                Q(wallet_code__icontains=query) |
                Q(keywords__icontains=query)
            )

        data = [{
            'id': str(w.id),
            'name': w.name,
            'name_en': w.name_en,
            'logo': w.logo.url if w.logo else None,
            'branch': w.branch.name if w.branch else None
        } for w in wallets[:20]]

        return JsonResponse({'results': data})


# ==================== AUTH VIEWS ====================

from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import AuthenticationForm


class DashboardLoginView(LoginView):
    """Custom login view for dashboard"""
    template_name = 'dashboard/auth/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('dashboard:home')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_superuser:
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)


class DashboardLogoutView(LogoutView):
    """Custom logout view"""
    next_page = 'dashboard:login'
