from django.contrib.auth.models import AbstractUser
from django.db import models
from cloudinary.models import CloudinaryField
import DateTime


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
    class GenderChoice(models.TextChoices):
        Male = "Male"
        Female = "Female"

    class Role(models.TextChoices):
        Doctor = "Doctor"
        Nurse = "Nurse"
        Patient = "Patient"

    phone_number = models.CharField(max_length=20, blank=True)
    sex = models.CharField(max_length=10, choices=GenderChoice, blank=True, null=True)
    avatar = CloudinaryField(blank=True, null=True)
    role = models.CharField(null=False, choices=Role, default=Role.Patient, max_length=10)

    # class Meta:
    #     abstract = True

    def __str__(self):
        return self.get_full_name()


class Doctor(User):
    speciality = models.CharField(max_length=30, default="Generally")

    class Meta:
        verbose_name = "Doctor"


class Nurse(User):
    department = models.CharField(max_length=100, null=True)

    class Meta:
        verbose_name = "Nurse"


class Patient(User):
    date_of_birth = models.DateField(null=True)

    class Meta:
        verbose_name = "Patient"


class DoctorSchedule(BaseModel):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)


class NurseSchedule(BaseModel):
    nurse = models.ForeignKey(Nurse, on_delete=models.CASCADE)
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)


class Appointment(BaseModel):
    class StatusChoices(models.TextChoices):
        PENDING = 'pending',
        APPROVED = 'approved',
        CANCELLED = 'cancelled',
        COMPLETE = 'completed',

    class TimeChoises(models.TextChoices):
        seven = "07:00:00",
        eight = '08:00:00'
        nine = '09:00:00'
        ten = '10:00:00'
        eleven = '11:00:00'
        thirteen = '13:00:00'
        fourteen = '14:00:00'
        fifteen = '15:00:00'
        sixteen = '16:00:00'
        seventeen = '17:00:00'

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, null=True, related_name='appointments', blank=True)
    selected_time = models.TimeField(choices=TimeChoises, default=TimeChoises.seven)
    selected_date = models.DateField()
    notify = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=StatusChoices, default=StatusChoices.PENDING)


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


class Service(BaseModel):
    name = models.CharField(max_length=25, null=False)
    price = models.IntegerField(null=False)

    def __str__(self):
        return self.name


class Prescription(BaseModel):  # Đơn thuốc
    appointment = models.OneToOneField(Appointment, related_name='prescription', primary_key=True,
                                       on_delete=models.CASCADE, null=False)
    symptom = models.CharField(max_length=255)  # Triệu chứng
    sick = models.CharField(max_length=255)
    services = models.ManyToManyField(Service, blank=True)
    medicine = models.ManyToManyField(Medicine, blank=True, through='PrescriptionMedicine')


class PrescriptionMedicine(BaseModel):
    medicine = models.ForeignKey(Medicine, related_name='prescription_medicine', on_delete=models.CASCADE, null=True)
    prescription = models.ForeignKey(Prescription, related_name="prescription_medicine", on_delete=models.CASCADE,
                                     null=True)
    quantity = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = ("medicine", "prescription")


class Bill(BaseModel):  # Hoắ đơn
    class statusChoices(models.TextChoices):
        unpaid = "unpaid"
        paid = "paid"

    prescription = models.OneToOneField(Prescription, related_name='bill', primary_key=True,
                                        on_delete=models.CASCADE, null=False)
    nurse = models.ForeignKey(Nurse, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=10, choices=statusChoices, default=statusChoices.unpaid)
    total = models.FloatField()
    zalopay_id = models.CharField(null=True, max_length=30)
