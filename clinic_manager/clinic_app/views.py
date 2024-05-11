from datetime import datetime

from django.conf import settings
from django.core.mail import send_mail
from django.core.serializers import serialize
from rest_framework import viewsets, generics, status, parsers, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from . import serializers, perms
from .dao import get_doctor, get_medicine, count_appointment_in_day, count_total, check_exist_appointment
from .models import *
from django.db.models import Q
from .perms import IsAdmin, OwnerAuthenticated, IsAdminOrDoctor, IsPatient, IsAdminOrPatient, IsDoctor, IsNurse


class MedicineViewSet(viewsets.ViewSet, generics.ListCreateAPIView, generics.DestroyAPIView):
    queryset = Medicine.objects.filter(active=True)
    serializer_class = serializers.MedicineSerializer

    # def get_permissions(self):
    #     if self.action in ['list']:
    #         return [IsAdminOrDoctor()]
    #     return [IsAdmin()]
    #     # return [permissions.AllowAny()]

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


class UserViewSet(viewsets.ViewSet, generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.filter(active=True)
    serializer_class = serializers.UserSerializer

    # permission_classes = [IsAdmin]

    def get_queryset(self):
        queryset = self.queryset
        if self.action.__eq__('list'):
            q = self.request.query_params.get('q')
            if q:
                queryset = queryset.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q))

        return queryset


# class DoctorViewSet(UserViewSet):
#     queryset = Doctor.objects.filter(active=True)
#     serializer_class = serializers.DoctorSerializer
#
#
# class NurseViewSet(UserViewSet):
#     queryset = Nurse.objects.filter(role='Nurse')
#     serializer_class = serializers.NurseSerializer


class PatientViewSet(viewsets.ViewSet, generics.ListCreateAPIView):
    queryset = Patient.objects.filter(active=True)
    serializer_class = serializers.PatientSerializer

    # def get_permissions(self):
    #     if self.action in ['get_appointments']:
    #         return [IsDoctor()]
    #     elif self.action in ['create']:
    #         return [permissions.AllowAny()]
    #     elif self.action in ['update']:
    #         return [OwnerAuthenticated()]
    #     return [IsAdmin()]

    @action(methods=['get'], url_path='get_appointments', detail=True)  # doctor see history apm of patient
    def get_appointments(self, request, pk):
        appoiments = self.get_object().appointments.filter(status__icontains='approved')

        # q = request.query_params.get('q')
        # if q:
        #     appoiments = appoiments.filter()

        return Response(serializers.AppointmentSerializer(appoiments, many=True).data,
                        status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True)
    def add_appointment(self, request, pk):
        patient = self.get_object()
        current_time = datetime.now()
        # Lấy thông tin của appointment từ request
        appointment_data = request.data
        if str(current_time.date()) < appointment_data["selected_date"] and str(current_time.time()) < appointment_data['selected_time']:
        # Thêm thông tin của patient vào appointment data
            if check_exist_appointment(date=appointment_data["selected_date"],time=appointment_data["selected_time"],patient=patient):
                return Response({"ms": "Appointment is exist"}, status=status.HTTP_400_BAD_REQUEST)
            appointment_data['patient'] = patient.id
            appointment_data['doctor'] = None

            # Tạo serializer với dữ liệu mới
            serializer = serializers.AppointmentSerializer(data=appointment_data)

            # Validate và lưu appointment
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response({"Time is not invalid"}, status=status.HTTP_400_BAD_REQUEST)


class AppointmentViewSet(viewsets.ViewSet, generics.ListCreateAPIView):
    queryset = Appointment.objects.filter(active=True)
    serializer_class = serializers.AppointmentSerializer

    # def get_permissions(self):
    #     if self.action in ['list', 'create']:
    #         return [IsNurse()]
    #     return [IsAdmin()]

    @action(methods=['patch'], url_path='approved', detail=True)
    def approve_appointment(self, request, pk=None):
        appointment = self.get_object()
        doctor = get_doctor(time=appointment.selected_time, date=appointment.selected_date)
        if count_appointment_in_day(date=appointment.selected_date) > settings.MAX_APPOINTMENT:
            return Response(
                {f"Number of appointment in {appointment.selected_date} is max ({settings.MAX_APPOINTMENT})"},
                status=status.HTTP_400_BAD_REQUEST)
        if doctor == None:
            return Response({f"No available doctor at {appointment.selected_date}.{appointment.selected_time}"},
                            status=status.HTTP_400_BAD_REQUEST)
        appointment.doctor = doctor
        appointment.status = 'approved'
        appointment.save()
        serializer = self.get_serializer(appointment)
        # Gửi email thông báo cho patient
        # message = f"Your appointment with ID {appointment.id} at {appointment.selected_date}.{appointment.selected_time} has been approved "
        # subject = "Approved appointment"
        # patient_email = appointment.patient.email
        # sender_email = settings.EMAIL_HOST_USER  # Email của sender
        # send_mail(subject, message, sender_email, [patient_email])
        message = "ok"
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['patch'], url_path='cancel', detail=True)  # patient cancel apm
    def cancel_appointment(self, request, pk=None):
        appointment = self.get_object()
        if appointment.status != 'approved':
            return Response({"error": "Only approved appointments can be cancel"}, status=status.HTTP_400_BAD_REQUEST)

        appointment.status = 'cancel'
        appointment.save()

        serializer = self.get_serializer(appointment)
        return Response(serializer.data, status=status.HTTP_200_OK)


@action(methods=['post'], url_path='create_prescription', detail=True)  # create new
def create_prescription(self, request, pk):
    appointment = self.get_object()  # lấy đối tượng hiện tại

    # Lấy thông tin của pre_me từ request
    pre_me = request.data

    # pre_me["medicine"] =  get_medicine(pre_me["medicine"]).__dict__
    pre_me['prescription'] = appointment.id  # gắn pre pre_me

    # Tạo serializer với dữ liệu mới
    serializer = serializers.PrescriptionSerializer(data=pre_me)

    # Validate và lưu appointment
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(serializer.data, status=status.HTTP_201_CREATED)


class PrescriptionViewSet(viewsets.ViewSet, generics.ListCreateAPIView):
    queryset = Prescription.objects.filter(active=True)
    serializer_class = serializers.PrescriptionSerializer

    @action(methods=['post'], url_path='pre_me', detail=True)  # create new
    def add_detail_medicine(self, request, pk):
        prescription = self.get_object()  # lấy đối tượng hiện tại

        # Lấy thông tin của pre_me từ request
        pre_me = request.data

        # pre_me["medicine"] =  get_medicine(pre_me["medicine"]).__dict__
        pre_me['prescription'] = prescription.appointment_id  # gắn pre pre_me

        # Tạo serializer với dữ liệu mới
        serializer = serializers.PrescriptionMedicineSerializer(data=pre_me)

        # Validate và lưu appointment
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=['post'], url_path='create_bill', detail=True)  # create new
    def create_bill(self, request, pk):
        prescription = self.get_object()  # lấy đối tượng hiện tại
        nurse = self.request.user
        # Lấy thông tin của pre_me từ request
        total = count_total(prescription)

        bill = request.data
        bill['prescription'] = prescription.appointment_id
        bill['nurse'] = nurse.id
        bill['total'] = total
        # pre_me["medicine"] =  get_medicine(pre_me["medicine"]).__dict__

        # Tạo serializer với dữ liệu mới
        serializer = serializers.BillSerializer(data=bill)

        # Validate và lưu appointment
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PrescriptionMedicineViewSet(viewsets.ViewSet, generics.ListCreateAPIView):
    queryset = PrescriptionMedicine.objects.filter(active=True)
    serializer_class = serializers.PrescriptionMedicineSerializer




import hmac, hashlib, urllib.parse, urllib.request, json, uuid
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
import hmac
import hashlib
import json
import requests


@csrf_exempt
def process_payment(request):
    if request.method == 'POST':
        # Nhận thông tin thanh toán từ yêu cầu POST
        payment_data = json.loads(request.body)
        amount = payment_data.get('amount')

        # Tạo orderId và requestId
        order_id = str(uuid.uuid4())
        request_id = str(uuid.uuid4())

        # Cấu hình thông tin MoMo
        endpoint = "https://test-payment.momo.vn/v2/gateway/api/create"
        access_key = "F8BBA842ECF85"
        secret_key = "K951B6PE1waDMi640xX08PD3vg6EkVlz"
        order_info = "Thanh chi phi kham benh"
        redirect_url = "http://127.0.0.1:8000/"  # Thay đổi URL redirect tại đây
        ipn_url = "http://127.0.0.1:8000"  # Thay đổi URL IPN tại đây

        # Tạo chuỗi chữ ký
        raw_signature = "accessKey=" + access_key + "&amount=" + str(amount) + "&extraData=" + "" \
                        + "&ipnUrl=" + ipn_url + "&orderId=" + order_id + "&orderInfo=" + order_info \
                        + "&partnerCode=MOMO" + "&redirectUrl=" + redirect_url + "&requestId=" + request_id \
                        + "&requestType=captureWallet"
        h = hmac.new(bytes(secret_key, 'ascii'), bytes(raw_signature, 'ascii'), hashlib.sha256)
        signature = h.hexdigest()

        # Tạo dữ liệu gửi đến MoMo
        data = {
            'partnerCode': 'MOMO',
            'partnerName': 'Test',
            'storeId': 'MomoTestStore',
            'requestId': request_id,
            'amount': str(amount),
            'orderId': order_id,
            'orderInfo': order_info,
            'redirectUrl': redirect_url,
            'ipnUrl': ipn_url,
            'lang': 'vi',
            'extraData': '',
            'requestType': 'captureWallet',
            'signature': signature
        }

        # Gửi yêu cầu thanh toán đến MoMo
        response = requests.post(endpoint, json=data)
        print(response.json())
        # Xử lý kết quả trả về từ MoMo
        if response.status_code == 200:
            response_data = response.json()
            if 'payUrl' in response_data:
                # Nếu thành công, trả về URL thanh toán cho frontend
                return JsonResponse({'payUrl': response_data['payUrl']})
            else:
                return JsonResponse({'error': 'Failed to process payment'})
        else:
            return JsonResponse({'error': 'Failed to communicate with MoMo'}, status=500)

    else:
        return JsonResponse({'error': 'Invalid request method'})