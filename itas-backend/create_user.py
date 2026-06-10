import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "itas.settings")
django.setup()
from core.models import User
user = User.objects.filter(email='test@example.com').first()
if not user:
    user = User.objects.create_user(username='test', email='test@example.com', password='test')
else:
    user.set_password('test')
    user.save()
print("User ready")
