import cloudinary
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import mark_safe
from .models import *
from django import forms
# from ckeditor_uploader.widgets import CKEditorUploadingWidget

class DoctorAdmin(UserAdmin):
    model = Doctor
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active',)}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    # fields = ['firstname', 'lastname']
    # fieldsets = ['firstname', 'lastname']

# class CourseForm(forms.ModelForm):
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

admin.site.register(Doctor,DoctorAdmin)
admin.site.register(Nurse)
admin.site.register(Admin)
admin.site.register(Patient)
admin.site.register(Schedule)
admin.site.register(DoctorSchedule)
admin.site.register(NurseSchedule)
admin.site.register(Medicine)
admin.site.register(Service)
admin.site.register(PrescriptionMedicine)
admin.site.register(Prescription)
admin.site.register(Appointment)










