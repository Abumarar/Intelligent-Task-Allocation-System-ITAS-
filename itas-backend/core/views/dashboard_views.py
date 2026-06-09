from rest_framework import viewsets, status, exceptions
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


class ReportsView(APIView):
    """View for generating system reports."""

    def get(self, request):
        if request.user.role != "PM":
            return Response(
                {"message": "Only Project Managers can view reports"},
                status=status.HTTP_403_FORBIDDEN,
            )

        user = request.user

        # 1. Task Allocation Stats — scoped to this PM's tasks
        pm_tasks = Task.objects.filter(created_by=user)
        total_tasks = pm_tasks.count()
        completed = pm_tasks.filter(status="COMPLETED").count()
        assigned = pm_tasks.filter(status="ASSIGNED").count()

        # 2. Workload Distribution — scoped to this PM's employees
        employees = Employee.objects.filter(manager=user)
        workload_data = [
            {"name": e.name, "workload": e.current_workload, "title": e.title}
            for e in employees
        ]

        # 3. Assignment History (last 30 days) — scoped to this PM's tasks
        last_30_days = timezone.now() - timezone.timedelta(days=30)
        assignments = TaskAssignment.objects.filter(
            assigned_at__gte=last_30_days, task__created_by=user
        ).count()

        return Response(
            {
                "task_stats": {
                    "total": total_tasks,
                    "completed": completed,
                    "assigned": assigned,
                    "completion_rate": round(
                        (completed / total_tasks * 100) if total_tasks else 0, 1
                    ),
                },
                "workload_distribution": workload_data,
                "recent_assignments": assignments,
            }
        )

class DashboardView(APIView):
    """Dashboard statistics endpoint."""

    def get(self, request):
        """Get dashboard statistics."""
        user = request.user

        if user.role == "EMPLOYEE":
            employee = getattr(user, "employee_profile", None)
            if not employee:
                return Response(
                    {
                        "active_tasks": 0,
                        "unassigned_tasks": 0,
                        "employee_capacity": 0,
                        "skills_coverage": 0,
                    }
                )

            active_tasks = TaskAssignment.objects.filter(
                employee=employee, status__in=["ASSIGNED", "IN_PROGRESS", "BLOCKED"]
            ).count()

            capacity = employee.current_workload

            data = {
                "active_tasks": active_tasks,
                "unassigned_tasks": 0,
                "employee_capacity": round(capacity, 1),
                "skills_coverage": 0,
            }
        else:
            # Filter stats by PM's data
            active_tasks = Task.objects.filter(
                created_by=user, status__in=["ASSIGNED", "IN_PROGRESS", "BLOCKED"]
            ).count()

            unassigned_tasks = Task.objects.filter(
                created_by=user, status__in=["UNASSIGNED", "DRAFT"]
            ).count()

            employees = Employee.objects.filter(manager=user)
            if employees.exists():
                total_capacity = sum(emp.current_workload for emp in employees)
                avg_capacity = total_capacity / employees.count()
            else:
                avg_capacity = 0

            # Skills coverage for PM's tasks
            pm_tasks = Task.objects.filter(created_by=user)
            tasks_with_skills = pm_tasks.exclude(task_skills__isnull=True).distinct()
            total_tasks = pm_tasks.count()

            if total_tasks > 0:
                skills_coverage = (tasks_with_skills.count() / total_tasks) * 100
            else:
                skills_coverage = 0

            data = {
                "active_tasks": active_tasks,
                "unassigned_tasks": unassigned_tasks,
                "employee_capacity": round(avg_capacity, 1),
                "skills_coverage": round(skills_coverage, 1),
            }

        serializer = DashboardStatsSerializer(data)
        return Response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def debug_media(request):
    """Debug view to check media file existence."""
    import os

    from django.conf import settings

    media_root = settings.MEDIA_ROOT
    media_url = settings.MEDIA_URL
    path = request.GET.get("path", "")

    exists = False
    full_path = ""
    folder_contents = []

    if path:
        full_path = os.path.join(media_root, path)
        exists = os.path.exists(full_path)

    # List media root contents
    try:
        if os.path.exists(media_root):
            folder_contents = os.listdir(media_root)
            # Check subfolders like 'cvs'
            cvs_path = os.path.join(media_root, "cvs")
            if os.path.exists(cvs_path):
                folder_contents.extend([f"cvs/{f}" for f in os.listdir(cvs_path)])
        else:
            folder_contents = ["Media Root does not exist"]
    except Exception as e:
        folder_contents = [str(e)]

    return Response(
        {
            "MEDIA_ROOT": media_root,
            "MEDIA_URL": media_url,
            "Requested Path": path,
            "Full Path": full_path,
            "Exists": exists,
            "Folder Contents": folder_contents,
            "DEBUG": settings.DEBUG,
            "Service": "ITAS Backend API",
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def debug_email(request):
    """Debug view to test email sending."""
    from django.conf import settings
    from django.core.mail import send_mail

    recipient = request.GET.get("recipient")
    if not recipient:
        return Response(
            {"message": "Please provide 'recipient' query parameter"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        send_mail(
            "Debug Email Test",
            f"This is a test email sent from {settings.EMAIL_HOST}",
            settings.DEFAULT_FROM_EMAIL,
            [recipient],
            fail_silently=False,
        )
        return Response(
            {
                "status": "SUCCESS",
                "message": f"Email sent to {recipient}",
                "config": {
                    "HOST": settings.EMAIL_HOST,
                    "PORT": settings.EMAIL_PORT,
                    "USER": (
                        settings.EMAIL_HOST_USER[:3] + "***"
                        if settings.EMAIL_HOST_USER
                        else "NOT SET"
                    ),
                    "TLS": settings.EMAIL_USE_TLS,
                },
            }
        )
    except Exception as e:
        return Response(
            {
                "status": "FAILED",
                "error": str(e),
                "config": {
                    "HOST": settings.EMAIL_HOST,
                    "PORT": settings.EMAIL_PORT,
                    "USER": (
                        settings.EMAIL_HOST_USER[:3] + "***"
                        if settings.EMAIL_HOST_USER
                        else "NOT SET"
                    ),
                    "TLS": settings.EMAIL_USE_TLS,
                },
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
