from rest_framework import permissions


class OwnerAuthenticated(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view) and request.user == obj.user


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        # Kiểm tra xem người dùng đã xác thực chưa
        if request.user.is_authenticated:
            return request.user.role == 'Admin'
        return False


class IsAdminOrDoctor(permissions.BasePermission):
    def has_permission(self, request, view):
        # Kiểm tra xem người dùng đã xác thực chưa
        if request.user.is_authenticated:
            return request.user.role == 'Admin' or request.user.role == 'Doctor'
        return False


class IsDoctor(permissions.BasePermission):
    def has_permission(self, request, view):
        # Kiểm tra xem người dùng đã xác thực chưa
        if request.user.is_authenticated:
            return request.user.role == 'Doctor'
        return False


class IsDoctorSearchOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        # Kiểm tra xem người dùng đã xác thực chưa
        if request.user.is_authenticated:
            # Kiểm tra xem người dùng có thuộc tính "role" và có giá trị là "Doctor" hay không
            return getattr(request.user, 'role', None) == 'Doctor' and view.action == 'list'
        # Nếu người dùng chưa xác thực, trả về False
        return False
