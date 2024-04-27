from django.contrib.auth.models import Permission

from clinic_manager.clinic_app.models import Admin

# Tạo một quyền mới cho admin để tìm kiếm nhân viên
can_search_employee = Permission.objects.create(
    codename='can_search_employee',
    name='Can search employee'
)


from django.contrib.auth.models import User

# Lấy người dùng là admin
admin_user = Admin.objects.filter(actite=True)

# Gán quyền tìm kiếm nhân viên cho admin
admin_user.user_permissions.add(can_search_employee)


from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.views import APIView
from rest_framework.response import Response

class CanSearchEmployee(BasePermission):
    def has_permission(self, request, view):
        # Kiểm tra xem người dùng có quyền tìm kiếm nhân viên không
        return request.user.has_perm('app_name.can_search_employee')

class EmployeeSearchAPIView(APIView):
    permission_classes = [IsAuthenticated, CanSearchEmployee]

    def get(self, request):
        # Thực hiện tìm kiếm nhân viên và trả về kết quả
        return Response({'message': 'Search results'})