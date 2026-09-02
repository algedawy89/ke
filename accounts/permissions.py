"""
Custom Permissions
"""
from rest_framework import permissions


class IsManager(permissions.BasePermission):
    """Only Manager can access"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_manager


class IsSupervisor(permissions.BasePermission):
    """Only Supervisor can access"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_supervisor


class IsManagerOrSupervisor(permissions.BasePermission):
    """Manager or Supervisor can access"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_manager or request.user.is_supervisor
        )


class IsAccountant(permissions.BasePermission):
    """Only Accountant can access"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_accountant


class IsCashier(permissions.BasePermission):
    """Only Cashier can access"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_cashier


class IsManagerOrAccountant(permissions.BasePermission):
    """Manager or Accountant can access"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_manager or request.user.is_accountant
        )


class CanManageUsers(permissions.BasePermission):
    """Can manage users (Manager or Supervisor)"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.can_manage_users()


class CanManageBranches(permissions.BasePermission):
    """Can manage branches"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.can_manage_branches()


class CanViewReports(permissions.BasePermission):
    """Can view reports"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.can_view_reports()


class IsOwnerOrManager(permissions.BasePermission):
    """Object-level permission: owner or manager"""
    def has_object_permission(self, request, view, obj):
        if request.user.is_manager:
            return True
        if hasattr(obj, 'cashier'):
            return obj.cashier == request.user
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        return False
