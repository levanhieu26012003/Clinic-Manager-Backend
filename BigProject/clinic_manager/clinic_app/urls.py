from django.contrib import admin
from django.urls import path, include
from rest_framework import routers

from . import views

r = routers.DefaultRouter()
r.register('medicine', views.MedicineViewSet, basename='Medicine')
r.register('doctor', views.DoctorViewSet, basename='Doctor')
r.register('Nurse', views.NurseViewSet, basename='nurse')
r.register('Patient', views.PatientViewSet, basename='Patient')


urlpatterns = [
    path('', include(r.urls))
]