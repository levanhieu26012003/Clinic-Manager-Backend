from django.db.models import Count, Sum
from datetime import datetime

from django.forms import model_to_dict

from .models import *


def count_patient_appointments_by_period(period, year):
    # lấy năm hiện tại
    # if year is None:
    #     year = datetime.now().year

    if period == 'month':
        annotations = {
            'period': models.functions.ExtractMonth('selected_date'),
        }
    elif period == 'quarter':
        annotations = {
            'period': models.functions.ExtractQuarter('selected_date'),
        }
    elif period == 'year':
        annotations = {
            'period': models.functions.ExtractYear('selected_date'),
        }
    else:
        raise ValueError("Invalid period. Choose from 'month', 'quarter', or 'year'.")

    # count
    appointments_by_period = (
        Appointment.objects
        .filter(selected_date__year=year)
        .annotate(**annotations)
        .values('period')
        .annotate(count=Count('id'))
        .order_by('period')
    )

    results = {item['period']: item['count'] for item in appointments_by_period}

    return results


def calculate_revenue_by_period(period, year):
    # lấy năm hiện tại


    if period == 'month':
        annotations = {
            'period': models.functions.ExtractMonth('prescription__appointment__selected_date'),
        }
    elif period == 'quarter':
        annotations = {
            'period': models.functions.ExtractQuarter('prescription__appointment__selected_date'),
        }
    elif period == 'year':
        annotations = {
            'period': models.functions.ExtractYear('prescription__appointment__selected_date'),
        }

    # sum
    revenue_by_period = (
        Bill.objects
        .filter(prescription__appointment__selected_date__year=year)
        .annotate(**annotations)
        .values('period')
        .annotate(revenue=Sum('total'))
        .order_by('period')
    )

    results = {item['period']: item['revenue'] for item in revenue_by_period}

    return results


def get_doctor(time, date):
    available_doctor_id = list(
        Appointment.objects.filter(selected_time=time, selected_date=date).values_list('doctor_id', flat=True))
    return Doctor.objects.exclude(id__in=available_doctor_id).first()


def get_medicine(id):
    return Medicine.objects.filter(id=id).all()


def count_appointment_in_day(date):
    return Appointment.objects.filter(selected_date=date).count()


def count_total(prescription):
    total_amount = 0

    services = prescription.services.all()

    # Tính tổng tiền của các dịch vụ
    for service in services:
        total_amount += service.price

        medicines = prescription.prescription_medicine.all()

        # Tính tổng tiền của các loại thuốc
        for medicine in medicines:
            total_amount += medicine.medicine.price * medicine.quantity

    return total_amount


def check_exist_appointment(date, time, patient):
    return Appointment.objects.filter(selected_date=date, selected_time=time, patient=patient).count() != 0


def get_dict_medicine_by_id(id):
    try:
        medicine = Medicine.objects.get(id=id)
        medicine_dict = model_to_dict(medicine)
        return medicine_dict
    except Medicine.DoesNotExist:
        return None