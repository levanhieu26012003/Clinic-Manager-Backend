from datetime import datetime
from django.utils import timezone
from pytz import timezone as tz
from django.conf import settings
from django.core.mail import send_mail
from django.core.serializers import serialize
from rest_framework import viewsets, generics, status, parsers, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from . import serializers, perms
from .dao import get_doctor, get_medicine, count_appointment_in_day, count_total, check_exist_appointment, \
    get_dict_medicine_by_id
from .models import *
from django.db.models import Q
from .perms import OwnerAuthenticated, IsPatient, IsDoctor, IsNurse


class MedicineViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Medicine.objects.filter(active=True)
    serializer_class = serializers.MedicineSerializer

    # permission_classes = [IsDoctor]

    def get_queryset(self):
        queryset = self.queryset
        q = self.request.query_params.get('q')
        if q:
            queryset = queryset.filter(name__icontains=q)

        return queryset


class ServiceViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Service.objects.filter(active=True)
    serializer_class = serializers.ServiceSerializer

    # permission_classes = [IsDoctor]

    def get_queryset(self):
        queryset = self.queryset
        q = self.request.query_params.get('q')
        if q:
            queryset = queryset.filter(name__icontains=q)

        return queryset


class PatientViewSet(viewsets.ViewSet, generics.ListCreateAPIView):
    queryset = Patient.objects.filter(active=True)
    serializer_class = serializers.PatientSerializer

    def get_queryset(self):
        queryset = self.queryset
        q = self.request.query_params.get('q')
        if q:
            queryset = queryset.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q))

        return queryset

    # def get_permissions(self):
    #     if self.action in ['create']:
    #         return [permissions.AllowAny()]
    #     elif self.action in ['get_appointments',]:
    #         return [IsDoctor()]
    #     return [OwnerAuthenticated()]

    @action(methods=['get'], url_path='get_appointments', detail=True)  # doctor see all appointments of patient
    def get_appointments(self, request, pk):
        appointment = self.get_object().appointments.filter(status='approved')

        return Response(serializers.AppointmentSerializer(appointment, many=True).data,
                        status=status.HTTP_200_OK)

    @action(methods=['get'], url_path='get_prescription', detail=True)  # doctor see history sick of patient
    def get_prescription(self, request, pk):
        patient_id = self.get_object().id
        patient_prescriptions = Prescription.objects.filter(appointment__patient_id=patient_id)

        return Response(serializers.PrescriptionSerializer(patient_prescriptions, many=True).data,
                        status=status.HTTP_200_OK)

    @action(methods=['post'],
            detail=True)  # Bệnh nhân tạo lịch khám của mình theo id. Json:  thời gian khám(ngày + giờ)
    def add_appointment(self, request, pk):
        patient = self.get_object()
        current_time_utc = timezone.now()
        vn_tz = tz('Asia/Ho_Chi_Minh')
        current_time = current_time_utc.astimezone(vn_tz)
        # Lấy thông tin của appointment từ request
        appointment_data = request.data
        booking_time = datetime.strptime(appointment_data["selected_time"], "%H:%M:%S")
        booking_date = datetime.strptime(appointment_data["selected_date"], "%Y-%m-%d")
        booking_datetime = datetime.combine(booking_date.date(), booking_time.time())
        booking_datetime = vn_tz.localize(booking_datetime)
        print(booking_datetime.timestamp() - current_time.timestamp())
        if booking_datetime.timestamp() - current_time.timestamp() < 3600:
            return Response({"ms": "Please book 1 hour in advance"}, status=status.HTTP_400_BAD_REQUEST)
        if booking_datetime.timestamp() - current_time.timestamp() > 3600 * 24 * 30:
            return Response({"ms": "Please do not book more than 30 days in advance"},
                            status=status.HTTP_400_BAD_REQUEST)

        # if str(current_time.date()) < appointment_data["selected_date"] and str(current_time.time()) < appointment_data[
        #     'selected_time']:
        if check_exist_appointment(date=appointment_data["selected_date"], time=appointment_data["selected_time"],
                                   patient=patient):
            return Response({"ms": "Appointment is exist"}, status=status.HTTP_400_BAD_REQUEST)
        appointment_data['patient'] = patient.id
        appointment_data['doctor'] = None
        # Tạo serializer với dữ liệu mới
        serializer = serializers.AppointmentSerializer(data=appointment_data)

        # Validate và lưu appointment
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AppointmentViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Appointment.objects.filter(active=True)
    serializer_class = serializers.AppointmentSerializer

    # def get_permissions(self):
    #     if self.action in ['list', 'create']:
    #         return [IsNurse()]
    #     return [IsAdmin()]

    def get_queryset(self):
        queryset = self.queryset
        q = self.request.query_params.get('q')
        if q:
            queryset = queryset.filter(status=q)

        return queryset

    @action(methods=['patch'], url_path='approved', detail=True)
    def approve_appointment(self, request, pk=None):
        appointment = self.get_object()
        doctor = get_doctor(time=appointment.selected_time, date=appointment.selected_date)
        if count_appointment_in_day(date=appointment.selected_date) > settings.MAX_APPOINTMENT:
            return Response(
                {f"Number of appointment in {appointment.selected_date} is max ({settings.MAX_APPOINTMENT})"},
                status=status.HTTP_400_BAD_REQUEST)
        if doctor == None:
            return Response({'ms': f"No available doctor at {appointment.selected_date}.{appointment.selected_time}"},
                            status=status.HTTP_400_BAD_REQUEST)
        appointment.doctor = doctor
        appointment.status = 'approved'
        appointment.save()
        serializer = self.get_serializer(appointment)
        # Gửi email thông báo cho patient
        message = f"Your appointment with ID {appointment.id} at {appointment.selected_date}.{appointment.selected_time} has been approved "
        subject = "Approved appointment"
        patient_email = appointment.patient.email
        sender_email = settings.EMAIL_HOST_USER  # Email của sender
        send_mail(subject, message, sender_email, [patient_email])

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['patch'], url_path='cancel', detail=True)  # patient cancel apm
    def cancel_appointment(self, request, pk=None):
        appointment = self.get_object()
        if appointment.status in ['approved', 'pending']:
            appointment.status = 'cancel'
            appointment.save()

            serializer = self.get_serializer(appointment)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"error": "Appointments can't  cancel"}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post'], url_path='create_prescription', detail=True)  # create new
    def create_prescription(self, request, pk):
        appointment = self.get_object()  # lấy đối tượng hiện tại
        # Lấy thông tin của pre_me từ request
        pre_me = request.data

        # pre_me["medicine"] =  get_medicine(pre_me["medicine"]).__dict__
        pre_me['appointment'] = appointment.id  # gắn pre pre_me
        print(pre_me)

        serializer = serializers.PrescritionSerializer(data=pre_me)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

        # return Response({"passs"}, status=status.HTTP_201_CREATED)

        # return Response("test", status=status.HTTP_201_CREATED)


class PrescriptionViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Prescription.objects.filter(active=True)
    serializer_class = serializers.PrescriptionSerializer

    @action(methods=['post'], url_path='add_prescription_medicine', detail=True)  # create new
    def add_prescription_medicine(self, request, pk):
        prescription = self.get_object()  # lấy đối tượng hiện tại
        prescription_medicine = request.data
        prescription_medicine['prescription'] = prescription.appointment_id
        serializer = serializers.PrescriptionMedicineSerializer(data=prescription_medicine)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=['post'], url_path='add_service', detail=True)  # create new
    def add_service(self, request, pk):
        prescription = self.get_object()  # lấy đối tượng hiện tại
        service_data = request.data
        try:
            service = Service.objects.get(id=service_data['id'])
        except Service.DoesNotExist:
            return Response({'error': 'Service not found'}, status=status.HTTP_404_NOT_FOUND)

            # Thêm dịch vụ vào đơn thuốc
        prescription.services.add(service)

        # Trả về dữ liệu của dịch vụ đã thêm cùng với mã trạng thái 201 (Created)
        serializer = serializers.ServiceSerializer(service)
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
        serializer = serializers.BillSerializer(data=bill)

        # Validate và lưu appointment
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PrescriptionMedicineViewSet(viewsets.ViewSet, generics.ListCreateAPIView):
    queryset = PrescriptionMedicine.objects.filter(active=True)
    serializer_class = serializers.PrescriptionMedicineSerializer


class BillViewSet(viewsets.ViewSet, generics.GenericAPIView):
    queryset = Bill.objects.filter(active=True)
    serializer_class = serializers.BillSerializer

    @action(methods=['patch'], detail=True)
    def comfirm_paid(self, request, pk):
        bill = self.get_object()
        if bill.status != 'unpaid':
            return Response({"error": "This bill was paid!!!"}, status=status.HTTP_400_BAD_REQUEST)

        bill.status = 'paid'
        bill.save()

        serializer = self.get_serializer(bill)
        return Response(serializer.data, status=status.HTTP_200_OK)

# import hmac, hashlib, urllib.parse, urllib.request, json, uuid
# from django.http import JsonResponse, HttpResponseBadRequest
# from django.views.decorators.csrf import csrf_exempt
# import hmac
# import hashlib
# import json
# import requests
#
#
# @csrf_exempt
# def process_payment(request):
#     if request.method == 'POST':
#         # Nhận thông tin thanh toán từ yêu cầu POST
#         payment_data = json.loads(request.body)
#         amount = payment_data.get('amount')
#
#         # Tạo orderId và requestId
#         order_id = str(uuid.uuid4())
#         request_id = str(uuid.uuid4())
#
#         # Cấu hình thông tin MoMo
#         endpoint = "https://test-payment.momo.vn/v2/gateway/api/create"
#         access_key = "F8BBA842ECF85"
#         secret_key = "K951B6PE1waDMi640xX08PD3vg6EkVlz"
#         order_info = "Thanh chi phi kham benh"
#         redirect_url = "http://127.0.0.1:8000/"  # Thay đổi URL redirect tại đây
#         ipn_url = "http://127.0.0.1:8000"  # Thay đổi URL IPN tại đây
#
#         # Tạo chuỗi chữ ký
#         raw_signature = "accessKey=" + access_key + "&amount=" + str(amount) + "&extraData=" + "" \
#                         + "&ipnUrl=" + ipn_url + "&orderId=" + order_id + "&orderInfo=" + order_info \
#                         + "&partnerCode=MOMO" + "&redirectUrl=" + redirect_url + "&requestId=" + request_id \
#                         + "&requestType=captureWallet"
#         h = hmac.new(bytes(secret_key, 'ascii'), bytes(raw_signature, 'ascii'), hashlib.sha256)
#         signature = h.hexdigest()
#
#         # Tạo dữ liệu gửi đến MoMo
#         data = {
#             'partnerCode': 'MOMO',
#             'partnerName': 'Test',
#             'storeId': 'MomoTestStore',
#             'requestId': request_id,
#             'amount': str(amount),
#             'orderId': order_id,
#             'orderInfo': order_info,
#             'redirectUrl': redirect_url,
#             'ipnUrl': ipn_url,
#             'lang': 'vi',
#             'extraData': '',
#             'requestType': 'captureWallet',
#             'signature': signature
#         }
#
#         # Gửi yêu cầu thanh toán đến MoMo
#         response = requests.post(endpoint, json=data)
#         print(response.json())
#         # Xử lý kết quả trả về từ MoMo
#         if response.status_code == 200:
#             response_data = response.json()
#             if 'payUrl' in response_data:
#                 # Nếu thành công, trả về URL thanh toán cho frontend
#                 return JsonResponse({'payUrl': response_data['payUrl']})
#             else:
#                 return JsonResponse({'error': 'Failed to process payment'})
#         else:
#             return JsonResponse({'error': 'Failed to communicate with MoMo'}, status=500)
#
#     else:
#         return JsonResponse({'error': 'Invalid request method'})
