from django.urls import path, include
from rest_framework import routers
from django.contrib.auth import  views as auth_views


from . import views

r = routers.DefaultRouter()
r.register('medicines', views.MedicineViewSet, basename='Medicines')
# r.register('doctors', views.DoctorViewSet, basename='Doctor')
# r.register('nurses', views.NurseViewSet, basename='nurse')
r.register('patients', views.PatientViewSet, basename='Patient')
r.register('appointments', views.AppointmentViewSet, basename='Appointment')
r.register('prescriptions', views.PrescriptionViewSet, basename='Prescription')
r.register('prescription_medicines', views.PrescriptionMedicineViewSet, basename='PrescriptionMedicine')
r.register('bills', views.BillViewSet, basename='Bill')


urlpatterns = [
    path('', include(r.urls)),
# facebook login
#     path('', views.home, name='home'),
    # path('login/', views.login, name='login'),
    # path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    # path('social-auth/', include('social_django.urls', namespace='social')),
]