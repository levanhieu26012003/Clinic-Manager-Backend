# from rest_framework import permissions
#
#
# class OwnerAuthenticated(permissions.IsAuthenticated):
#     def has_object_permission(self, request, view, obj):
#         return self.has_permission(request, view) and request.user == obj.user
#
#
# class IsAdmin(permissions.BasePermission):
#     def has_permission(self, request, view):
#         # Kiểm tra xem người dùng đã xác thực chưa
#         if request.user.is_authenticated:
#             return request.user.role == 'Admin'
#         return False
#
#
# class IsDoctor(permissions.BasePermission):
#     def has_permission(self, request, view):
#         # Kiểm tra xem người dùng đã xác thực chưa
#         if request.user.is_authenticated:
#             return request.user.role == 'Doctor'
#         return False
#
#
# class IsNurse(permissions.BasePermission):
#     def has_permission(self, request, view):
#         # Kiểm tra xem người dùng đã xác thực chưa
#         if request.user.is_authenticated:
#             return request.user.role == 'Nurse'
#         return False
#
#
# class IsPatient(permissions.BasePermission):
#     def has_permission(self, request, view):
#         # Kiểm tra xem người dùng đã xác thực chưa
#         if request.user.is_authenticated:
#             return request.user.role == 'Patient'
#         return False
#
#
# class IsAdminOrDoctor(permissions.BasePermission):
#     def has_permission(self, request, view):
#         # Kiểm tra xem người dùng đã xác thực chưa
#         if request.user.is_authenticated:
#             return request.user.role == 'Doctor' or request.user.role == 'Admin'
#         return False
#
#
# class IsAdminOrPatient(permissions.BasePermission):
#     def has_permission(self, request, view):
#         if request.user.is_authenticated:
#             return request.user.role == 'Patient' or request.user.role == 'Admin'
#         return False
#


from rest_framework import permissions

class OwnerAuthenticated(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return super().has_object_permission(request, view, obj) and request.user == obj.user


class IsAdminOrRole(permissions.BasePermission):
    allowed_roles = []

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return request.user.role in self.allowed_roles or request.user.role == 'Admin'
        return False


class IsAdmin(IsAdminOrRole):
    allowed_roles = ['Admin']


class IsDoctor(IsAdminOrRole):
    allowed_roles = ['Doctor']


class IsNurse(IsAdminOrRole):
    allowed_roles = ['Nurse']


class IsPatient(IsAdminOrRole):
    allowed_roles = ['Patient']


class IsAdminOrDoctor(IsAdminOrRole):
    allowed_roles = ['Admin', 'Doctor']


class IsAdminOrPatient(IsAdminOrRole):
    allowed_roles = ['Admin', 'Patient']
