import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'itas.settings')
django.setup()

from core.urls import router
for prefix, viewset, basename in router.registry:
    if prefix == 'employees':
        print("EmployeeViewSet module:", viewset.__module__)
