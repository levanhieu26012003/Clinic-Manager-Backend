from celery import shared_task
from django.utils import timezone
import random
from pytz import timezone as tz

import logging

from clinic_app.models import Appointment, Patient

from clinic_manager import settings

logger = logging.getLogger(__name__)

# @shared_task
# def update_appointment_status():
#
#
#     appointments = Appointment.objects.filter(selected_date__lte=today, status='approved')
#     for appointment in appointments:
#         if appointment.selected_date < today or (appointment.selected_date == today and appointment.selected_time__hour <= current_time.hour + 1):
#             appointment.status = 'cancel'
#             appointment.save()


from django.core.mail import send_mail


@shared_task(bind=True)
def send_notification_email(self):
    current_time_utc = timezone.now()
    vn_tz = tz('Asia/Ho_Chi_Minh')
    now = current_time_utc.astimezone(vn_tz)
    soon = now + timezone.timedelta(hours=1)  # Kiểm tra lịch hẹn diễn ra trong 30 phút tới

    list_apm = Appointment.objects.filter(
        selected_date=soon.date(),
        selected_time__range=(now.time(), soon.time()),
        status=Appointment.StatusChoices.APPROVED,
        notify=False
    )

    for appointment in list_apm:
        try:
            send_mail(
                'Thông báo lịch hẹn sắp diễn ra',
                f'Xin chào {appointment.patient.username},\n\nLịch hẹn của bạn tại phòng khám sẽ diễn ra vào {appointment.selected_time}.',
                settings.EMAIL_HOST_USER,
                [appointment.patient.email],
                fail_silently=False,  # Đặt fail_silently=False để lỗi được ném ra nếu có
            )
            appointment.notify = True
            appointment.save()
        except Exception as e:
            # Log lỗi nếu gửi email thất bại
            logger.error(f'Error sending email to {appointment.patient.email}: {e}')

    return "DONE"


@shared_task(bind=True)
def change_name(self):
    rd = random.randint(1, 100)
    pt = Patient.objects.get(id=4)
    pt.first_name = str(rd)
    pt.save()
    return "done"
