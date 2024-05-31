from rest_framework import serializers
from .models import *


class ItemSerializer(serializers.ModelSerializer):
    # def to_representation(self, instance):
    #     rep = super().to_representation(instance)
    #     if rep['avatar'] is not None:
    #         print(rep['avatar'])
    #         rep['avatar'] = instance.avatar.url
    #     return rep

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        avatar_url = representation.get('avatar')
        if avatar_url and avatar_url.startswith('image/upload/'):
            # Remove 'image/upload/' prefix
            avatar_url = avatar_url.replace('image/upload/', '', 1)
            representation['avatar'] = avatar_url
        return representation


class PatientSerializer(ItemSerializer):
    class Meta:
        model = Patient
        fields = ['id', 'first_name', 'last_name', 'username', 'password', 'phone_number', 'sex',
                  'avatar', 'role', 'date_of_birth', 'email']
        extra_kwargs = {'password': {'write_only': True}}  # Ẩn mật khẩu khi trả về

    def create(self, validated_data):
        user = Patient(**validated_data)
        user.set_password(validated_data['password'])
        user.save()

        return user


class AppointmentSerializer(serializers.ModelSerializer):
    patient = PatientSerializer

    class Meta:
        model = Appointment
        fields = ['id', 'selected_time', 'selected_date', 'patient', 'doctor', 'status']


class MedicineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medicine
        fields = ['id', 'name', 'price', 'unit', 'usage']


class PrescriptionMedicineSerializer(serializers.ModelSerializer):
    medicine = MedicineSerializer

    class Meta:
        model = PrescriptionMedicine
        fields = ['id', 'medicine', 'prescription', 'quantity']


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name', 'price']


class PrescriptionSerializer(serializers.ModelSerializer):
    prescription_medicine = PrescriptionMedicineSerializer(many=True, required=False)

    services = ServiceSerializer(many=True, required=False)

    class Meta:
        model = Prescription
        fields = ['appointment', 'symptom', 'sick', 'services', 'prescription_medicine']
        extra_kwargs = {
            'services': {'required': False},
            'prescription_medicine': {'required': False},
        }

    # def create(self, validated_data):
    #     data = validated_data.pop('prescription_medicine', [])
    #     prescription = Prescription.objects.create(**validated_data)
    #     for d in data:
    #         medicine = Medicine.objects.get(id=d['b']['id'])
    #         PrescriptionMedicine.objects.create(prescription=prescription, medicine=medicine, quantity=d['quantity'])
    #     return prescription


class BillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bill
        fields = ['prescription', 'nurse', 'status', 'total','zalopay_id']


class CreatePaymentSerializer(serializers.Serializer):
    amount = serializers.IntegerField(required=True)
    description = serializers.CharField(required=True)