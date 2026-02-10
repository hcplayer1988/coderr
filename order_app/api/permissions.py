"""Custom permissions for order API endpoints."""
from rest_framework import permissions


class IsBusinessUserOfOrder(permissions.BasePermission):
    """
    Custom permission to only allow business users who are part of the order to update it.
    """
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user is the business_user of the order.
        """
        try:
            if request.user.type != 'business':
                return False
        except AttributeError:
            return False
        
        return obj.business_user == request.user


