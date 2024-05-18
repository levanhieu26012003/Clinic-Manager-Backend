from datetime import datetime

import cloudinary
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count
from django.db.models.functions import ExtractMonth
from django.template.response import TemplateResponse
from django.urls import path

from .dao import count_patient_appointments_by_period, calculate_revenue_by_period
from .models import *

class MyAdminSite(admin.AdminSite):
    site_header = 'Hiếu Hậu'

    def get_urls(self):
        return [path('stats/', self.stats_view)] + super().get_urls()

    def stats_view(self, request):
        # now = datetime.now()
        # year_selected = now.year
        # stats = Appointment.objects.annotate(month=ExtractMonth('selected_time_date')).values('month').annotate(
        #     count=Count('month'))
        year = request.GET.get('year')
        period = request.GET.get('period','month')
        patient_stats = count_patient_appointments_by_period(period=period,year=year)
        revenue_stats = calculate_revenue_by_period(period=period,year=year)

        context = {
            'patient_stats': patient_stats,
            'revenue_stats': revenue_stats,
            'period': period,
            "year": year
        }
        return TemplateResponse(request, 'admin/stats1.html', context)






admin_site = MyAdminSite(name='iCourse')


class DoctorAdmin(UserAdmin):
    model = Doctor
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info',
         {'fields': ('first_name', 'last_name', 'email', 'sex', 'phone_number', 'avatar', 'speciality')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'role')}),
        # ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )


class NurseAdmin(UserAdmin):
    model = Nurse
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info',
         {'fields': ('first_name', 'last_name', 'email', 'sex', 'phone_number', 'avatar', 'department')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'role')}),
    )


class PatientAdmin(UserAdmin):
    model = Patient
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info',
         {'fields': ('first_name', 'last_name', 'email', 'sex', 'phone_number', 'avatar', 'date_of_birth')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'role')}),
    )


class MedicineAdmin(admin.ModelAdmin):
    search_fields = ["name"]



# fields = ['firstname', 'lastname']
# fieldsets = ['firstname', 'lastname']

# class UserForm(forms.ModelForm):
#     description = forms.CharField(widget=CKEditorUploadingWidget)
#
#     class Meta:
#         model = Course
#         fields = '__all__'


# class MyCourseAdmin(admin.ModelAdmin):
#     list_display = ['id', 'name', 'created_date', 'updated_date', 'active']
#     search_fields = ['name', 'description']
#     list_filter = ['id', 'created_date', 'name']
#     readonly_fields = ['my_image']
#     form = CourseForm
#
#     def my_image(self, instance):
#         if instance:
#             if instance.image is cloudinary.CloudinaryResource:
#                 return mark_safe(f"<img width='120' src='{instance.image.url}' />")
#
#             return mark_safe(f"<img width='120' src='/static/{instance.image.name}' />")
#
#     class Media:
#         css = {
#             'all': ('/static/css/style.css', )
#         }

admin_site.register(Doctor, DoctorAdmin)
admin_site.register(Nurse, NurseAdmin)
admin_site.register(Bill)
admin_site.register(Patient, PatientAdmin)
admin_site.register(Schedule)
admin_site.register(DoctorSchedule)
admin_site.register(NurseSchedule)
admin_site.register(Medicine, MedicineAdmin)
admin_site.register(PrescriptionMedicine)
admin_site.register(Prescription)
admin_site.register(User)
admin_site.register(Appointment)
admin_site.register(Service)


# admin.site.register(Doctor, DoctorAdmin)
# admin.site.register(Nurse, NurseAdmin)
# admin.site.register(Bill)
# admin.site.register(Patient, PatientAdmin)
# admin.site.register(Schedule)
# admin.site.register(DoctorSchedule)
# admin.site.register(NurseSchedule)
# admin.site.register(Medicine, MedicineAdmin)
# admin.site.register(PrescriptionMedicine)
# admin.site.register(Prescription)
