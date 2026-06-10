from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import viewsets, status, exceptions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate, get_user_model
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from core.models import User, Employee, Project, Task, TaskAssignment, Skill, AuditLog, CV
from core.serializers import UserSerializer, EmployeeSerializer, ProjectSerializer, TaskSerializer, TaskAssignmentSerializer, TaskMatchSerializer
from core.services.audit_service import AuditService
from core.services.matching_engine import MatchingEngine
from core.services.cv_parser import CVParser
from core.services.skill_extractor import SkillExtractor
from core.authentication import generate_jwt_token


class AuthView(APIView):
    """Authentication endpoints."""

    permission_classes = [AllowAny]
    # authentication_classes default to settings (JWT) which is fine for login as it handles Anonymous

    def get(self, request):
        """Verify token and return current user."""
        if not request.user.is_authenticated:
            return Response(
                {"message": "Invalid or expired token"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user_serializer = UserSerializer(request.user)
        user_data = user_serializer.data
        user_data["id"] = str(user_data["id"])

        return Response({"user": user_data})

    def post(self, request):
        """Login endpoint."""
        email_or_username = (request.data.get("email") or "").strip()
        password = (request.data.get("password") or "").strip()

        if not email_or_username or not password:
            return Response(
                {"message": "Please provide both email/username and password"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 1. Try to find user by email or username
        user = User.objects.filter(
            Q(email__iexact=email_or_username) | Q(username__iexact=email_or_username)
        ).first()

        if not user:
            return Response(
                {"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )

        # Use Django's authenticate to respect auth backends properly
        # Some projects authenticate with username, not email.
        authed = authenticate(request, username=user.username, password=password)

        if not authed:
            return Response(
                {"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )

        # Generate token
        token = generate_jwt_token(authed)

        # Serialize user
        user_serializer = UserSerializer(authed)
        user_data = user_serializer.data
        user_data["id"] = str(user_data["id"])  # frontend compatibility

        return Response({"token": token, "user": user_data}, status=status.HTTP_200_OK)

    def patch(self, request):
        """Update current user profile (Name, Email, Password)."""
        if not request.user.is_authenticated:
            return Response(
                {"message": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user = request.user
        data = request.data

        # Update Name
        if "name" in data:
            name_parts = data["name"].strip().split()
            user.first_name = name_parts[0] if name_parts else ""
            user.last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        # Update Email
        if "email" in data:
            new_email = data["email"].strip().lower()
            if new_email and new_email != user.email:
                if User.objects.filter(email=new_email).exclude(id=user.id).exists():
                    return Response(
                        {"message": "Email already in use"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                user.email = new_email

        # Update Password
        if "password" in data:
            new_password = data["password"].strip()
            if len(new_password) < 6:
                return Response(
                    {"message": "Password must be at least 6 characters"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user.set_password(new_password)

        user.save()

        # Serialize updated user
        user_serializer = UserSerializer(user)
        user_data = user_serializer.data
        user_data["id"] = str(user_data["id"])

        return Response({"user": user_data, "message": "Profile updated successfully"})

