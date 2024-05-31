import cloudinary
import logging

logger = logging.getLogger(__name__)

from django.http import JsonResponse
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from pytz import timezone as tz
from django.conf import settings
from django.core.mail import send_mail
from rest_framework import viewsets, generics, status, parsers, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from . import serializers, perms
from .dao import get_doctor, count_appointment_in_day, count_total, check_exist_appointment, \
    check_exist_pre_me
from .models import *
from django.db.models import Q
from .perms import OwnerAuthenticated, IsPatient, IsDoctor, IsNurse
import cloudinary.uploader


class MedicineViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Medicine.objects.filter(active=True)
    serializer_class = serializers.MedicineSerializer

    permission_classes = [IsDoctor]

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

    # def to_representation(self, instance):
    #     representation = super().to_representation(instance)
    #     logger.debug(f"Avatar URL: {representation['avatar']}")
    #     return representation
    #
    # def save(self, *args, **kwargs):
    #     if self.avatar:
    #         self.avatar = self.avatar.url
    #     super().save(*args, **kwargs)

    # def get_permissions(self):
    #     if self.action in ['create']:
    #         return [permissions.AllowAny()]
    #     elif self.action in ['get_appointments', 'get_prescriptions', 'list']:
    #         return [IsDoctor()]
    #     return [OwnerAuthenticated()]  # change password, add_appointment, change_infor, forget_pass

    def get_queryset(self):
        queryset = self.queryset
        q = self.request.query_params.get('q')
        if q:
            queryset = queryset.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q))

        return queryset

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

    @action(methods=['post'], url_path='add_appointment',
            detail=True)  # Bệnh nhân tạo lịch khám của mình theo id. Json:  thời gian khám(ngày + giờ)
    def add_appointment(self, request, pk):
        appointment_data = request.data
        patient = self.get_object()
        current_time_utc = timezone.now()
        vn_tz = tz('Asia/Ho_Chi_Minh')
        current_time = current_time_utc.astimezone(vn_tz)
        # Lấy thông tin của appointment từ request
        booking_time = datetime.strptime(appointment_data["selected_time"], "%H:%M:%S")
        booking_date = datetime.strptime(appointment_data["selected_date"], "%Y-%m-%d")
        booking_datetime = datetime.combine(booking_date.date(), booking_time.time())
        booking_datetime = vn_tz.localize(booking_datetime)

        if booking_datetime.timestamp() - current_time.timestamp() < 3600:
            return Response({"ms": "Please book 1 hour in advance"}, status=status.HTTP_400_BAD_REQUEST)
        if booking_datetime.timestamp() - current_time.timestamp() > 3600 * 24 * 30:
            return Response({"ms": "Please do not book more than 30 days in advance"},
                            status=status.HTTP_400_BAD_REQUEST)

        if check_exist_appointment(date=appointment_data["selected_date"], time=appointment_data["selected_time"],
                                   patient=patient):
            return Response({"ms": "Appointment is exist"}, status=status.HTTP_400_BAD_REQUEST)

        appointment['patient'] = patient.id
        # appointment_data['doctor'] = None
        print(appointment)

        # Tạo serializer với dữ liệu mới
        serializer = serializers.AppointmentSerializer(data=appointment)

        # Validate và lưu appointment
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['patch'], url_path='forget_password', url_name='change_password')
    def forget_password(self, request):
        user = Patient.objects.get(id=request.user.id)
        new_password = get_random_string(length=8)

        user.set_password(new_password)
        user.save()

        message = f"Your new password is {new_password} "
        subject = "New password"
        patient_email = user.email
        sender_email = settings.EMAIL_HOST_USER  # Email của sender
        send_mail(subject, message, sender_email, [patient_email])

        return Response(serializers.PatientSerializer(user).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['patch'], url_path='change_password', url_name='change_password')
    def change_password(self, request):
        user = Patient.objects.get(id=self.request.user.id)
        old_password = request.data.get('old_password', None)
        new_password = request.data.get('new_password', None)
        if user.check_password(old_password):
            user.set_password(new_password)
            user.save()
            return Response({'ms': 'Password changed successfully'}, status=status.HTTP_200_OK)
        else:
            return Response({'ms': 'Invalid old password'}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['patch'], url_path='change_infor', detail=False)
    def change_infor(self, request):
        user = request.user
        for k, v in request.data.items():
            if k == 'avatar':
                new_avatar = cloudinary.uploader.upload(v)
                user.avatar = new_avatar['secure_url']
            else:
                setattr(user, k, v)
        user.save()

        return Response(serializers.PatientSerializer(user).data)


class AppointmentViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Appointment.objects.filter(active=True)
    serializer_class = serializers.AppointmentSerializer

    # def get_permissions(self):
    #     if self.action in ['cancel']:
    #         return [IsPatient()]
    #     if self.action in ['create_prescription']:
    #         return [IsDoctor()]
    #     return [IsNurse()]

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
        now = datetime.now()
        message = f"Your appointment with ID {appointment.id} at {appointment.selected_date}.{appointment.selected_time} has been approved at {now}."
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
        appointment.status = 'completed'
        appointment.save()
        # Lấy thông tin của pre_me từ request
        pre_me = request.data

        pre_me['appointment'] = appointment.id  # gắn pre pre_me
        serializer = serializers.PrescriptionSerializer(data=pre_me)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PrescriptionViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Prescription.objects.filter(active=True)
    serializer_class = serializers.PrescriptionSerializer

    # def get_permissions(self):
    #     if self.action in ['create_bill']:
    #         return [IsNurse()]
    #     return [IsDoctor()]

    @action(methods=['post'], url_path='add_prescription_medicine', detail=True)  # create new
    def add_prescription_medicine(self, request, pk):
        prescription = self.get_object()  # lấy đối tượng hiện tại
        prescription_medicine = request.data
        pre_me_db = check_exist_pre_me(me=prescription_medicine['medicine'], pre=prescription.appointment_id)
        if pre_me_db:
            pre_me_db.quantity += prescription_medicine['quantity']
            pre_me_db.save()
            return Response(serializers.PrescriptionMedicineSerializer(pre_me_db).data, status=status.HTTP_201_CREATED)

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


from time import time
from datetime import datetime
import json, hmac, hashlib, urllib.request, urllib.parse
import urllib.parse, urllib.request


class ZaloPayViewset(viewsets.ViewSet):
    @csrf_exempt
    @action(methods=['patch', 'post'], url_path='create_bill', detail=False)
    def create_order(self, request):
        bill = Bill.objects.get(prescription_id=request.data['id'])
        transID = bill.prescription_id
        amount = bill.total
        app_time = int(round(time() * 1000))
        order = {
            "app_id": settings.ZALOPAY_APP_ID,
            "app_trans_id": "{:%y%m%d}_{}_{}".format(datetime.today(), transID, app_time),
            # mã giao dich có định dạng yyMMdd_xxxx
            "app_user": "user123",
            "app_time": app_time,  # miliseconds
            "embed_data": json.dumps({}),
            "item": json.dumps([{}]),
            "amount": int(amount),
            "description": "Thanh toan phong kham " + str(transID),
            "bank_code": "zalopayapp",
            "callback_url": "https://3303-171-243-48-141.ngrok-free.app/"
        }

        # app_id|app_trans_id|app_user|amount|apptime|embed_data|item
        data = "{}|{}|{}|{}|{}|{}|{}".format(order["app_id"], order["app_trans_id"], order["app_user"],
                                             order["amount"], order["app_time"], order["embed_data"], order["item"])

        order["mac"] = hmac.new(settings.ZALOPAY_KEY1.encode(), data.encode(), hashlib.sha256).hexdigest()

        response = urllib.request.urlopen(url=settings.ZALOPAY_ENDPOINT_CREATE,
                                          data=urllib.parse.urlencode(order).encode())
        result = json.loads(response.read())

        if result['return_code'] == 1:
            bill.zalopay_id = order["app_trans_id"]
            bill.save()
            return JsonResponse(result)
        if result['return_code'] == 2:
            return JsonResponse(result, status=status.HTTP_400_BAD_REQUEST)
        return JsonResponse({"ms": "fail!!!"}, status=status.HTTP_400_BAD_REQUEST)

    @csrf_exempt
    @action(methods=['patch', 'post'], url_path='callback', detail=False)
    def callback(self, request):
        result = {}
        try:
            cbdata = request.data
            print(cbdata)
            mac = hmac.new(settings.ZALOPAY_KEY2.encode(), cbdata['data'].encode(), hashlib.sha256).hexdigest()

            # kiểm tra callback hợp lệ (đến từ ZaloPay server)
            if mac != cbdata['mac']:
                # callback không hợp lệ
                result['return_code'] = -1
                result['return_message'] = 'mac not equal'
            else:
                # thanh toán thành công
                # merchant cập nhật trạng thái cho đơn hàng
                dataJson = json.loads(cbdata['data'])
                print("update order's status = success where app_trans_id = " + dataJson['app_trans_id'])
                bill = Bill.objects.get(zalopay_id=dataJson['app_trans_id'])
                bill.status = 'paid'
                bill.save()
                result['return_code'] = 1
                result['return_message'] = 'success'
        except Exception as e:
            result['return_code'] = 0  # ZaloPay server sẽ callback lại (tối đa 3 lần)
            result[' e'] = str(e)

        # thông báo kết quả cho ZaloPay server
        return JsonResponse(result)

    @csrf_exempt
    @action(methods=['patch'], url_path='check_bill', detail=False)
    def check_bill(self, request):
        bill = Bill.objects.get(prescription_id=request.data['id'])
        transID = bill.zalopay_id

        params = {
            "app_id": settings.ZALOPAY_APP_ID,
            "app_trans_id": transID  # Input your app_trans_id"
        }

        data = "{}|{}|{}".format(settings.ZALOPAY_APP_ID, params["app_trans_id"],
                                 settings.ZALOPAY_KEY1)  # app_id|app_trans_id|key1
        params["mac"] = hmac.new(settings.ZALOPAY_KEY1.encode(), data.encode(), hashlib.sha256).hexdigest()

        response = urllib.request.urlopen(url=settings.ZALOPAY_ENDPOINT_QUERY,
                                          data=urllib.parse.urlencode(params).encode())
        result = json.loads(response.read())

        if result['return_code'] == 1:
            bill.status = 'paid'
            bill.save()
            return JsonResponse(result)
        if result['return_code'] == 3:
            return JsonResponse(result, status=status.HTTP_400_BAD_REQUEST)
        return JsonResponse({"ms": "fail!!!"}, status=status.HTTP_400_BAD_REQUEST)


#
# from django.shortcuts import render
# from django.contrib.auth.decorators import login_required
#
#
# def login(request):
#     return render(request, 'login.html')
#
#
# @login_required
# def home(request):
#     return render(request, 'home.html')
from django.shortcuts import render

# def test(request):
#     test_func.delay()
#     return HttpResponse("Done")
