"""
API Views for ITAS
"""
import threading
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model, authenticate
from django.db.models import Q

from rest_framework import viewsets, status, exceptions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from core.models import Employee, Task, TaskAssignment, Skill, CV
from core.serializers import (
    UserSerializer, EmployeeSerializer, TaskSerializer,
    TaskMatchSerializer, TaskAssignmentSerializer, DashboardStatsSerializer
)
from core.authentication import generate_jwt_token
from core.services.cv_parser import CVParser
from core.services.skill_extractor import SkillExtractor
from core.services.matching_engine import MatchingEngine

User = get_user_model()


class AuthView(APIView):
    """Authentication endpoints."""
    permission_classes = [AllowAny]
    authentication_classes = []  # No authentication required for login

    def post(self, request):
        """Login endpoint."""
        email_or_username = (request.data.get("email") or "").strip()
        password = request.data.get("password")

        if not email_or_username or not password:
            return Response(
                {"message": "Email/username and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Normalize (helps if user types spaces/case differences)
        email_or_username_norm = email_or_username.lower()

        # Try to find the user by email OR username (case-insensitive)
        user = User.objects.filter(
            Q(email__iexact=email_or_username_norm) | Q(username__iexact=email_or_username_norm)
        ).first()

        if not user:
            return Response(
                {"message": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Use Django's authenticate to respect auth backends properly
        # Some projects authenticate with username, not email.
        authed = authenticate(request, username=user.username, password=password)

        if not authed:
            return Response(
                {"message": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Generate token
        token = generate_jwt_token(authed)

        # Serialize user
        user_serializer = UserSerializer(authed)
        user_data = user_serializer.data
        user_data["id"] = str(user_data["id"])  # frontend compatibility

        return Response(
            {"token": token, "user": user_data},
            status=status.HTTP_200_OK
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def seed_db(request):
    """Emergency endpoint to seed users if build script fails."""
    from django.contrib.auth import get_user_model
    from core.models import Employee
    User = get_user_model()
    
    created_users = []
    
    # Create PM
    if not User.objects.filter(email='pm@itas.com').exists():
        User.objects.create_user(username='pm', email='pm@itas.com', password='pm123', role='PM')
        created_users.append('PM')
        
    # Create Admin
    if not User.objects.filter(email='admin@itas.com').exists():
        User.objects.create_superuser(username='admin', email='admin@itas.com', password='admin123', role='PM')
        created_users.append('Admin')
    
    return Response({'message': 'Seeding complete', 'created': created_users})

class EmployeeViewSet(viewsets.ModelViewSet):
    """Employee endpoints."""
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer

    def get_queryset(self):
        """Filter employees based on user role."""
        user = self.request.user
        queryset = Employee.objects.all()

        if user.role == "EMPLOYEE":
            # Employees can only see their own profile
            employee = getattr(user, "employee_profile", None)
            if employee:
                queryset = queryset.filter(id=employee.id)
            else:
                queryset = queryset.none()

        return queryset

    def create(self, request, *args, **kwargs):
        """Create new employee and associated user."""
        # Check permissions (only PM can create employees)
        if request.user.role != "PM":
            return Response(
                {"message": "Only Project Managers can add employees"},
                status=status.HTTP_403_FORBIDDEN
            )

        data = request.data
        email = data.get("email")
        name = data.get("name")
        title = data.get("title")

        if not email or not name:
            return Response(
                {"message": "Email and name are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user exists
        if User.objects.filter(email=email).exists():
            return Response(
                {"message": "User with this email already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                # Create User
                username = email.split("@")[0]
                # Ensure unique username
                if User.objects.filter(username=username).exists():
                    import uuid
                    username = f"{username}_{uuid.uuid4().hex[:4]}"

                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password="password123",  # Default password
                    first_name=name.split(" ")[0],
                    last_name=" ".join(name.split(" ")[1:]) if " " in name else "",
                    role="EMPLOYEE"
                )

                # Create Employee
                employee = Employee.objects.create(
                    user=user,
                    title=title,
                    email=email
                )

                serializer = self.get_serializer(employee)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {"message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def perform_destroy(self, instance):
        """Delete employee and associated user."""
        if self.request.user.role != "PM":
            raise exceptions.PermissionDenied("Only Project Managers can remove employees.")

        user = instance.user
        instance.delete()
        user.delete()

    @action(detail=True, methods=["post"], url_path="cv")
    def upload_cv(self, request, pk=None):
        """Upload CV for employee."""
        employee = self.get_object()

        if "file" not in request.FILES:
            return Response(
                {"message": "No file provided"},
                status=status.HTTP_400_BAD_REQUEST
            )

        file = request.FILES["file"]

        # Validate file type
        if not file.name.lower().endswith(".pdf"):
            return Response(
                {"message": "Only PDF files are supported"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate PDF
        parser = CVParser()
        if not parser.is_valid_pdf(file):
            return Response(
                {"message": "Invalid PDF file"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create or update CV record
        cv, created = CV.objects.get_or_create(employee=employee)
        cv.file = file
        cv.status = "PROCESSING"
        cv.error_message = None
        cv.save()

        # Process CV in background thread
        def process_cv():
            try:
                cv.refresh_from_db()
                with cv.file.open("rb") as pdf_file:
                    extracted_text = parser.extract_text_from_pdf(pdf_file)

                if not extracted_text:
                    cv.status = "FAILED"
                    cv.error_message = "Could not extract text from PDF"
                    cv.save()
                    return

                cv.extracted_text = extracted_text
                cv.status = "READY"
                cv.processed_at = timezone.now()
                cv.save()

                extractor = SkillExtractor()
                skills_data = extractor.extract_skills(extracted_text)

                with transaction.atomic():
                    Skill.objects.filter(employee=employee, source="CV").delete()

                    for skill_data in skills_data:
                        skill_name = extractor.normalize_skill_name(skill_data["name"])
                        Skill.objects.create(
                            employee=employee,
                            name=skill_name,
                            source="CV",
                            confidence_score=skill_data["confidence_score"]
                        )

            except Exception as e:
                cv.status = "FAILED"
                cv.error_message = str(e)
                cv.save()

        thread = threading.Thread(target=process_cv)
        thread.daemon = True
        thread.start()

        return Response({
            "message": "CV uploaded and processing started",
            "status": "PROCESSING"
        })

    @action(detail=False, methods=["get"], url_path="my-profile")
    def get_my_profile(self, request):
        """Get current employee's profile and tasks."""
        user = request.user

        if user.role != "EMPLOYEE":
            return Response(
                {"message": "This endpoint is only for employees"},
                status=status.HTTP_403_FORBIDDEN
            )

        employee = getattr(user, "employee_profile", None)
        if not employee:
            return Response(
                {"message": "Employee profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        employee_data = EmployeeSerializer(employee).data

        assignments = TaskAssignment.objects.filter(
            employee=employee,
            status__in=["ASSIGNED", "IN_PROGRESS"]
        ).select_related("task")

        tasks_data = []
        for assignment in assignments:
            task = assignment.task
            tasks_data.append({
                "id": str(task.id),
                "title": task.title,
                "status": assignment.status,
                "priority": task.priority,
                "suitability_score": assignment.suitability_score,
                "due_date": task.due_date.isoformat() if task.due_date else None,
            })

        return Response({
            "employee": employee_data,
            "tasks": tasks_data,
            "workload": employee.current_workload
        })


class TaskViewSet(viewsets.ModelViewSet):
    """Task endpoints."""
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    pagination_class = None  # Disable pagination for now, return all results

    def get_queryset(self):
        """Filter tasks based on user role."""
        user = self.request.user
        queryset = Task.objects.all()

        if user.role == "EMPLOYEE":
            employee = getattr(user, "employee_profile", None)
            if employee:
                assigned_task_ids = TaskAssignment.objects.filter(
                    employee=employee
                ).values_list("task_id", flat=True)
                queryset = queryset.filter(id__in=assigned_task_ids)

        return queryset.order_by("-created_at")

    def perform_create(self, serializer):
        """Create task with current user as creator."""
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["get"], url_path="matches")
    def get_matches(self, request, pk=None):
        """Get recommended employee matches for a task."""
        task = self.get_object()

        engine = MatchingEngine()
        matches = engine.find_best_matches(task, limit=10, min_score=50.0)

        serializer = TaskMatchSerializer(matches, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="assign")
    def assign_task(self, request, pk=None):
        """Assign task to an employee."""
        task = self.get_object()
        employee_id = request.data.get("employee_id")

        if not employee_id:
            return Response(
                {"message": "employee_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response(
                {"message": "Employee not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        engine = MatchingEngine()
        score = engine.calculate_suitability_score(
            employee,
            task,
            task.required_skills
        )

        assignment, created = TaskAssignment.objects.get_or_create(
            task=task,
            employee=employee,
            defaults={
                "suitability_score": score,
                "status": "ASSIGNED"
            }
        )

        if not created:
            assignment.suitability_score = score
            assignment.status = "ASSIGNED"
            assignment.save()

        task.status = "ASSIGNED"
        task.save()

        serializer = TaskAssignmentSerializer(assignment)
        return Response(serializer.data)


class DashboardView(APIView):
    """Dashboard statistics endpoint."""

    def get(self, request):
        """Get dashboard statistics."""
        user = request.user

        if user.role == "EMPLOYEE":
            employee = getattr(user, "employee_profile", None)
            if not employee:
                return Response({
                    "active_tasks": 0,
                    "unassigned_tasks": 0,
                    "employee_capacity": 0,
                    "skills_coverage": 0
                })

            active_tasks = TaskAssignment.objects.filter(
                employee=employee,
                status__in=["ASSIGNED", "IN_PROGRESS"]
            ).count()

            capacity = employee.current_workload

            data = {
                "active_tasks": active_tasks,
                "unassigned_tasks": 0,
                "employee_capacity": round(capacity, 1),
                "skills_coverage": 0
            }
        else:
            active_tasks = Task.objects.filter(
                status__in=["ASSIGNED", "IN_PROGRESS"]
            ).count()

            unassigned_tasks = Task.objects.filter(
                status="UNASSIGNED"
            ).count()

            employees = Employee.objects.all()
            if employees.exists():
                total_capacity = sum(emp.current_workload for emp in employees)
                avg_capacity = total_capacity / employees.count()
            else:
                avg_capacity = 0

            tasks_with_skills = Task.objects.exclude(task_skills__isnull=True).distinct()
            total_tasks = Task.objects.count()

            if total_tasks > 0:
                skills_coverage = (tasks_with_skills.count() / total_tasks) * 100
            else:
                skills_coverage = 0

            data = {
                "active_tasks": active_tasks,
                "unassigned_tasks": unassigned_tasks,
                "employee_capacity": round(avg_capacity, 1),
                "skills_coverage": round(skills_coverage, 1)
            }

        serializer = DashboardStatsSerializer(data)
        return Response(serializer.data)
