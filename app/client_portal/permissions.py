from rest_framework.permissions import BasePermission

from config.authentication.services import FirstAccessService

from .selectors import is_manager, is_staff_member


class CredentialsUpToDate(BasePermission):
    """Blocks business endpoints until a seeded account changes its credentials.

    Authentication endpoints stay reachable so the holder can complete the step.
    """

    message = 'Complete the first access before using the portal.'

    def has_permission(self, request, view):
        return not FirstAccessService.is_pending(request.user)


class IsPortalUser(BasePermission):
    """Any authenticated portal user that is not a Django administrator."""

    message = 'Portal access is required.'

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated and not user.is_staff):
            return False
        return CredentialsUpToDate().has_permission(request, view)


class IsPortalStaff(BasePermission):
    """Group STAFF or STAFF_MANAGER; never a Django Admin account."""

    message = 'Platform staff access is required.'

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated and not user.is_staff and is_staff_member(user)):
            return False
        return CredentialsUpToDate().has_permission(request, view)


class IsStaffManager(BasePermission):
    message = 'STAFF_MANAGER access is required.'

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated and not user.is_staff and is_manager(user)):
            return False
        return CredentialsUpToDate().has_permission(request, view)
