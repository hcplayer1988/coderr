"""Custom permissions for reviews API endpoints."""
from rest_framework import permissions


class IsReviewOwner(permissions.BasePermission):
    """
    Custom permission to only allow review owners to update/delete their reviews.
    """
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user is the reviewer (owner) of the review.
        """
        return obj.reviewer == request.user