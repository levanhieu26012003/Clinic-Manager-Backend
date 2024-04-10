from django.contrib.auth.models import AbstractUser
from django.db import models
from cloudinary.models import CloudinaryField
import DateTime

GENDER_CHOISES = (
    ("MALE", "MALE"),
    ("FEMALE", "FEMALE"),
)


class BaseModel(models.Model):
    created_date = models.DateTimeField(auto_now_add=True, null=True)
    updated_date = models.DateTimeField(auto_now=True, null=True)
    active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class Schedule(BaseModel):
    time_start = models.DateTimeField()
    time_end = models.DateTimeField()

    def __str__(self):
        return str(self.time_start) + " to " + str(self.time_end)


class User(AbstractUser, BaseModel):
    first_name = models.CharField(null=False, max_length=30)
    last_name = models.CharField(null=False, max_length=30)
    phone_number = models.CharField(max_length=20)
    sex = models.CharField(max_length=10, choices=GENDER_CHOISES, null=True)
    avatar = CloudinaryField(null=True)

    # class Meta:
    #     abstract = True

    def __str__(self):
        return self.get_full_name()

class Admin(User):
    pass


class Doctor(User):
    speciality = models.CharField(max_length=30, default="Generally")


class Nurse(User):
    department = models.CharField(max_length=100, null=True)


class DoctorSchedule(BaseModel):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)


class NurseSchedule(BaseModel):
    Nurse = models.ForeignKey(Nurse, on_delete=models.CASCADE)
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)


class Patient(User):
    date_of_birth = models.DateField(null=True)


class Appointment(BaseModel):
    class StatusChoices(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        CANCELLED = 'cancelled', 'Cancelled'
        COMPLETE = "complete", "Complete"
    # class TimeChoice(models.TextChoices):
    #     Time = '80', 'Pending'


    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    nurse = models.ForeignKey(Nurse, on_delete=models.CASCADE, null=True)
    time = models.TimeField()
    date = models.DateField()
    order_number = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=StatusChoices, default=StatusChoices.PENDING)


class Service(BaseModel):
    name = models.CharField(max_length=25, null=False)
    price = models.IntegerField(null=False)

    def __str__(self):
        return self.name


class Medicine(BaseModel):
    class TypeOfMedicine(models.TextChoices):
        capsule = "capsule"  # viên uống mềm
        pill = "pill"  # viên uống cứng
        tablet = "tablet"  # vỉ
        patch = "patch"  # miếng dán
        liquid = "liquid"  # siro
        drop = "drop"  # thuốc nhỏ
        needle = "needle"  # dạng tiêm

    name = models.CharField(max_length=255, unique=True)
    price = models.FloatField()
    usage = models.CharField(max_length=255)
    unit = models.CharField(max_length=20, choices=TypeOfMedicine, default=TypeOfMedicine.capsule)

    def __str__(self):
        return str(self.name) + " (" + str(self.unit) + ")"
        return str(self.name) + " (" + str(self.unit) + ")"


class Prescription(BaseModel):  # Đơn thuốc
    appointment = models.OneToOneField(Appointment, related_name='prescription', primary_key=True,
                                       on_delete=models.CASCADE, null=False)
    symptom = models.CharField(max_length=255)  # Triệu chứng
    sick = models.CharField(max_length=255)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)


class Bill():  # Hoắ đơn
    prescription = models.OneToOneField(Prescription, related_name='prescription', primary_key=True,
                                        on_delete=models.CASCADE, null=False)
    nurse = models.ForeignKey(Nurse, on_delete=models.SET_NULL, null=True)
    total = models.FloatField()


class PrescriptionMedicine(BaseModel):
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, null=True)
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, null=True)
    quantity = models.PositiveSmallIntegerField()
