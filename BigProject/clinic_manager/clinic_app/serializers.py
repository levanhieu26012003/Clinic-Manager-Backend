from rest_framework import serializers
from .models import *


class MedicineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medicine
        fields = ['id', 'name', 'price', 'unit']


class ItemSerializer(serializers.ModelSerializer):
    # pass
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['avatar'] = instance.avatar.url

        return rep


class DoctorSerializer(ItemSerializer):
    class Meta:
        model = Doctor
        fields = ['id', 'first_name', 'last_name', 'speciality', 'phone_number', 'sex', 'avatar']


class NurseSerializer(ItemSerializer):
    class Meta:
        model = Nurse
        fields = ['id', 'first_name', 'last_name', 'department', 'phone_number', 'sex', 'avatar']


class PatientSerializer(ItemSerializer):
    class Meta:
        model = Patient
        fields = ['id', 'first_name', 'last_name', 'date_of_birth', 'phone_number', 'sex', 'avatar']

# class LessonDetailsSerializer(LessonSerializer):
#     tags = TagSerializer(many=True)
#
#     class Meta:
#         model = LessonSerializer.Meta.model
#         fields = LessonSerializer.Meta.fields + ['content', 'tags']


# class AuthenticatedLessonDetailsSerializer(LessonDetailsSerializer):
#     liked = serializers.SerializerMethodField()
#
#     def get_liked(self, lesson):
#         return lesson.like_set.filter(active=True).exists()
#
#     class Meta:
#         model = LessonDetailsSerializer.Meta.model
#         fields = LessonDetailsSerializer.Meta.fields + ['liked']


# class UserSerializer(serializers.ModelSerializer):
#     def to_representation(self, instance):
#         rep = super().to_representation(instance)
#         rep['avatar'] = instance.avatar.url
#
#         return rep
#
#     def create(self, validated_data):
#         data = validated_data.copy()
#
#         user = User(**data)
#         user.set_password(data["password"])
#         user.save()
#
#         return user
#
#     class Meta:
#         model = User
#         fields = ['id', 'first_name', 'last_name', 'email', 'username', 'password', 'avatar']
#         extra_kwargs = {
#             'password': {
#                 'write_only': True
#             }
#         }
