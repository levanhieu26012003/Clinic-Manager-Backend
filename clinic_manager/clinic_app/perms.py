from rest_framework import permissions


class OwnerAuthenticated(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return super().has_object_permission(request, view, obj) and request.user.id == obj.id


class BaseRole(permissions.BasePermission):
    allowed_roles = []

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return request.user.role in self.allowed_roles
        return False


class IsDoctor(BaseRole):
    allowed_roles = ['Doctor']


class IsNurse(BaseRole):
    allowed_roles = ['Nurse']


class IsPatient(BaseRole):
    allowed_roles = ['Patient']
