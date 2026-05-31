import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'itas.settings')

app = Celery('itas')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
