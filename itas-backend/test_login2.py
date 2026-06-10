import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "itas.settings")
django.setup()

from core.models import User
from core.authentication import generate_jwt_token
from core.serializers import UserSerializer
from django.contrib.auth import authenticate

user = User.objects.filter(email='test@example.com').first()
print("User is", user)
if user:
    # Test authenticate
    # Notice we need a request object for authenticate, or we can just pass None in older django, but let's pass None
    authed = authenticate(request=None, username=user.username, password='test')
    print("Authed:", authed)
    
    if authed:
        token = generate_jwt_token(authed)
        print("Token:", token)
        serializer = UserSerializer(authed)
        print("Serializer:", serializer.data)
