import requests

# 1. Login
login_data = {
    "email": "admin@example.com", # wait, what is the admin email? Or I can just create a user.
}
# Actually, it's easier to just use Django test client!
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'itas.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()
user = User.objects.filter(role="PM").first()
if not user:
    user = User.objects.create_user(username="testpm", email="pm@test.com", password="pwd", role="PM")

client = Client()
client.force_login(user)

cv_content = b"""
Name: Mohammad Abumarar
Email: mo.abumarar@gmail.com
Title: Software Engineer

Skills:
React, Python, Leadership, Django
"""
file = SimpleUploadedFile("cv.txt", cv_content, content_type="text/plain")

response = client.post('/api/employees/analyze/', {'file': file})
print("STATUS:", response.status_code)
print("RESPONSE:", response.json())

