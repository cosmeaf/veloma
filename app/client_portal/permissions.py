from rest_framework.permissions import BasePermission

from .selectors import is_manager, is_staff_member


class IsPortalUser(BasePermission):
    """Any authenticated portal user that is not a Django administrator."""

    message = 'Portal access is required.'

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and not user.is_staff)


class IsPortalStaff(BasePermission):
    """Group STAFF or STAFF_MANAGER; never a Django Admin account."""

    message = 'Platform staff access is required.'

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and not user.is_staff and is_staff_member(user))


class IsStaffManager(BasePermission):
    message = 'STAFF_MANAGER access is required.'

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and not user.is_staff and is_manager(user))
