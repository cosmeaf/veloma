from rest_framework.permissions import BasePermission


class IsFrontendStaff(BasePermission):
    message = 'Platform staff access is required.'

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and not user.is_staff and user.groups.filter(name='STAFF').exists())


class IsFrontendUser(BasePermission):
    message = 'Customer access is required.'

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and not user.is_staff and user.groups.filter(name='USER').exists())
