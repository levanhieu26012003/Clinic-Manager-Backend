from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Thiết lập môi trường của Django cho Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinic_manager.settings')

app = Celery('clinic_manager')
app.conf.update(timezone='Asia/Ho_Chi_Minh')

# Nạp các thiết lập từ file settings của Django
app.config_from_object('django.conf:settings', namespace='CELERY')
# Tự động nạp các tác vụ từ tất cả các ứng dụng đã cài đặt trong Django
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
