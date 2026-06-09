import os
import re

VIEWS_FILE = "itas-backend/core/views.py"
VIEWS_DIR = "itas-backend/core/views"

os.makedirs(VIEWS_DIR, exist_ok=True)

with open(VIEWS_FILE, "r") as f:
    content = f.read()

# Common imports for all files
common_imports = """from rest_framework import viewsets, status, exceptions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate, get_user_model
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from core.models import User, Employee, Project, Task, TaskAssignment, Skill, AuditLog, CV
from core.serializers import UserSerializer, EmployeeSerializer, ProjectSerializer, TaskSerializer, TaskAssignmentSerializer, AuditLogSerializer, TaskMatchSerializer
from core.services.audit_service import AuditService
from core.services.matching_engine import MatchingEngine
from core.services.cv_parser import CVParser
from core.services.skill_extractor import SkillExtractor
"""

# Extract classes using regex.
classes = re.split(r'\nclass ', '\n' + content)
header = classes[0]
classes = classes[1:]

files = {
    "auth_views.py": ["AuthView"],
    "employee_views.py": ["EmployeeViewSet"],
    "project_views.py": ["ProjectViewSet"],
    "task_views.py": ["TaskViewSet"],
    "dashboard_views.py": ["DashboardView", "ReportsView"]
}

for filename, class_names in files.items():
    with open(os.path.join(VIEWS_DIR, filename), "w") as f:
        f.write(common_imports + "\n\n")
        for cls in classes:
            cls_name = cls.split('(', 1)[0].split(':', 1)[0].strip()
            if cls_name in class_names:
                f.write("class " + cls)

# Write __init__.py
with open(os.path.join(VIEWS_DIR, "__init__.py"), "w") as f:
    f.write("from .auth_views import AuthView\n")
    f.write("from .employee_views import EmployeeViewSet\n")
    f.write("from .task_views import TaskViewSet\n")
    f.write("from .project_views import ProjectViewSet\n")
    f.write("from .dashboard_views import DashboardView, ReportsView\n")

# Remove old views.py
os.remove(VIEWS_FILE)
print("Split successful")
