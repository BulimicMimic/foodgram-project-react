from django.contrib.auth import get_user_model
from rest_framework import permissions

User = get_user_model()


class IsCurrentUserOrAdminOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or request.user.role == User.Role.admin
                or obj.id == request.user)


class IsOwnerOrAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or request.user.role == User.Role.admin
                or obj.author == request.user)
