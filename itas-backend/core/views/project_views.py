from core.models import (
    CV,
    AuditLog,
    Employee,
    Project,
    Skill,
    Task,
    TaskAssignment,
    User,
)
from core.serializers import (
    EmployeeSerializer,
    ProjectSerializer,
    TaskAssignmentSerializer,
    TaskMatchSerializer,
    TaskSerializer,
    UserSerializer,
)
from core.services.audit_service import AuditService
from core.services.cv_parser import CVParser
from core.services.matching_engine import MatchingEngine
from core.services.skill_extractor import SkillExtractor
from django.contrib.auth import authenticate, get_user_model
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import exceptions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class ProjectViewSet(viewsets.ModelViewSet):
    """Project endpoints."""

    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def get_queryset(self):
        """Filter projects based on user role."""
        user = self.request.user
        queryset = Project.objects.select_related("manager")

        if user.role == "PM":
            # PMs see only their projects
            queryset = queryset.filter(manager=user)
        else:
            # Employees - what should they see? All active projects?
            # Or projects they have tasks in?
            # For now, let's say Employees see active projects to know what's going on.
            if self.action == "list":
                queryset = queryset.filter(status="ACTIVE")
            else:
                # Can only see details, not edit
                pass

        return queryset

    def perform_create(self, serializer):
        """Create project with current user as manager."""
        serializer.save(manager=self.request.user)
