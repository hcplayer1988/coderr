"""Custom permissions for profile API endpoints."""
from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of a profile to edit it.

    Read access is allowed for any authenticated user.
    """

    def has_object_permission(self, request, view, obj):
        """Allow read for all, write only for owner."""
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.user == request.user
