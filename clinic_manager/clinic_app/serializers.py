from rest_framework import serializers
from .models import *




class ItemSerializer(serializers.ModelSerializer):
    # pass
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if rep['avatar'] is not None:
            rep['avatar'] = instance.avatar.url

        return rep
class MedicineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medicine
        fields = ['id', 'name', 'price', 'unit','usage']


class UserSerializer(ItemSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'username', 'password', 'phone_number', 'sex',
                  'avatar','role']



class DoctorSerializer(UserSerializer):
    class Meta:
        model = Doctor
        fields = UserSerializer.Meta.fields + ['speciality']

    def create(self, validated_data):
        user = Doctor(**validated_data)
        user.set_password(validated_data['password'])
        user.save()

        return user

class NurseSerializer(UserSerializer):
    class Meta:
        model = Nurse
        fields = UserSerializer.Meta.fields + ['department']



class PatientSerializer(ItemSerializer):
    class Meta:
        model = Patient
        fields = UserSerializer.Meta.fields + ['date_of_birth']


