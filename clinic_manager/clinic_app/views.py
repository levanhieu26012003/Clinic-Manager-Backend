from rest_framework import viewsets, generics, status, parsers, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from . import serializers, perms
from .models import *
from django.db.models import Q
from .perms import IsAdmin, OwnerAuthenticated, IsDoctorSearchOnly, IsAdminOrDoctor


class MedicineViewSet(viewsets.ViewSet, generics.ListCreateAPIView, generics.DestroyAPIView):
    queryset = Medicine.objects.filter(active=True)
    serializer_class = serializers.MedicineSerializer

    # def get_permissions(self):
    #     # if self.action in ['list']:
    #     #     return [IsAdminOrDoctor()]
    #     # return [IsAdmin()]
    #     return [permissions.AllowAny()]

    def get_queryset(self):
        queryset = self.queryset
        if self.action.__eq__('list'):
            q = self.request.query_params.get('q')
            if q:
                queryset = queryset.filter(name__icontains=q)

        return queryset

    # @action(methods=['patch'], url_path='')
    # def

    @action(detail=True, methods=['patch'])
    def update_info(self, request, pk=None):
        # Lấy đối tượng cần cập nhật
        instance = self.get_object()

        # Tạo serializer với dữ liệu mới từ yêu cầu PATCH
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Lưu lại dữ liệu đã cập nhật
        serializer.save()

        # Trả về dữ liệu đã cập nhật trong response
        return Response(serializer.data)


class UserViewSet(viewsets.ViewSet, generics.ListCreateAPIView):
    queryset = User.objects.filter(active=True)
    serializer_class = serializers.UserSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        queryset = self.queryset
        if self.action.__eq__('list'):
            q = self.request.query_params.get('q')
            if q:
                queryset = queryset.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q))

        return queryset


class DoctorViewSet(UserViewSet):
    queryset = Doctor.objects.filter(active=True)
    serializer_class = serializers.DoctorSerializer

class NurseViewSet(UserViewSet):
    queryset = Nurse.objects.filter(role='Nurse')
    serializer_class = serializers.NurseSerializer

class PatientViewSet(UserViewSet):
    queryset = Patient.objects.filter(active=True)
    serializer_class = serializers.PatientSerializer
