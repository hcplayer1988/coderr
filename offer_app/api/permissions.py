"""Custom permissions for offer app."""
from rest_framework import permissions


class IsOfferOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an offer to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        """
        Check if the user is the owner of the offer.
        """
        return obj.user == request.user
    
