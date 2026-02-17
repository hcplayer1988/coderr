"""Custom permissions for reviews API endpoints."""
from rest_framework import permissions


class IsReviewOwner(permissions.BasePermission):
    """
    Custom permission to only allow review owners to edit/delete.

    Only the reviewer (owner) of a review can update or delete it.
    """

    def has_object_permission(self, request, view, obj):
        """Check if user is the reviewer (owner) of the review."""
        return obj.reviewer == request.user