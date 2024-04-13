# tạo data cho bảng Medicine
from django.db import migrations


def create_default_data(apps, schema_editor):
    MyModel = apps.get_model('clinic_app', 'Medicine')
    MyModel.objects.create(name='Men lợi khuẩn', price='20', unit='pill', usage="Tiêu hóa tốt")


class Migration(migrations.Migration):
    dependencies = [
        ('clinic_app', '0003_nurse_department_patient_date_of_birth'),
    ]

    operations = [
        migrations.RunPython(create_default_data),
    ]
