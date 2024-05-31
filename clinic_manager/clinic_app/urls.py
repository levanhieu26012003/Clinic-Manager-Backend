from django.urls import path, include
from rest_framework import routers
from django.contrib.auth import  views as auth_views


from . import views

r = routers.DefaultRouter()
r.register('medicines', views.MedicineViewSet, basename='Medicines')
r.register('patients', views.PatientViewSet, basename='Patient')
r.register('appointments', views.AppointmentViewSet, basename='Appointment')
r.register('prescriptions', views.PrescriptionViewSet, basename='Prescription')
r.register('services', views.ServiceViewSet, basename='Service')
r.register('bills', views.BillViewSet, basename='Bill')
r.register('zalopay', views.ZaloPayViewset, basename='ZaloPay')


urlpatterns = [
    path('', include(r.urls)),
    # path('test/', views.test_func, name='test '),

    # facebook login
#     path('', views.home, name='home'),
#     path('login/', views.login, name='login'),
#     path('logout/', auth_views.LogoutView.as_view(), name='logout'),
#     path('social-auth/', include('social_django.urls', namespace='social')),
]