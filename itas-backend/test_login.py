import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "itas.settings")
django.setup()

from core.models import User
from core.authentication import generate_jwt_token
from core.serializers import UserSerializer

try:
    user = User.objects.first()
    if not user:
        print("No users found.")
    else:
        print(f"Testing for user {user.username}")
        token = generate_jwt_token(user)
        print("Token generated successfully.")
        
        user_serializer = UserSerializer(user)
        user_data = user_serializer.data
        user_data["id"] = str(user_data["id"])
        print("Serialization successful.", user_data)
except Exception as e:
    import traceback
    traceback.print_exc()
