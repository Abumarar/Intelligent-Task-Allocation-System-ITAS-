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
    # authentication_classes default to settings (JWT) which is fine for login as it handles Anonymous

    def get(self, request):
        """Verify token and return current user."""
        if not request.user.is_authenticated:
            return Response(
                {"message": "Invalid or expired token"},
                status=status.HTTP_401_UNAUTHORIZED
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
                status=status.HTTP_400_BAD_REQUEST
            )

        # 1. Try to find user by email or username
        user = User.objects.filter(
            Q(email__iexact=email_or_username) | 
            Q(username__iexact=email_or_username)
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

    def patch(self, request):
        """Update current user profile (Name, Email, Password)."""
        if not request.user.is_authenticated:
            return Response(
                {"message": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED
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
                        status=status.HTTP_400_BAD_REQUEST
                    )
                user.email = new_email

        # Update Password
        if "password" in data:
            new_password = data["password"].strip()
            if len(new_password) < 6:
                 return Response(
                    {"message": "Password must be at least 6 characters"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.set_password(new_password)

        user.save()
        
        # Serialize updated user
        user_serializer = UserSerializer(user)
        user_data = user_serializer.data
        user_data["id"] = str(user_data["id"])

        return Response({"user": user_data, "message": "Profile updated successfully"})


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
        else:
            # PMs see only their managed employees
            queryset = queryset.filter(manager=user)

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
                    manager=request.user, # Assign current PM as manager
                    title=title,
                    email=email
                )

                # Add initial skills if provided
                skills = data.get("skills", [])
                if skills and isinstance(skills, list):
                    for skill_name in skills:
                        Skill.objects.create(
                            employee=employee,
                            name=skill_name,
                            source="MANUAL", # Created via form (even if auto-filled)
                            confidence_score=1.0
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

    @action(detail=False, methods=["post"], url_path="analyze")
    def analyze_cv(self, request):
        """
        Analyze a CV file and return extracted details (Name, Email, Title)
        for pre-filling the employee creation form.
        """
        if "file" not in request.FILES:
            return Response(
                {"message": "No file provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        file = request.FILES["file"]
        
        # Parse PDF
        parser = CVParser()
        is_pdf = parser.is_valid_pdf(file)
        is_docx = parser.is_valid_docx(file)
        
        if not (is_pdf or is_docx):
             return Response(
                {"message": "Only PDF and DOCX files are supported"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Read file
        if hasattr(file, 'read'):
            file_content = file.read()
            file.seek(0)
        else:
            file_content = file
            
        try:
            extracted_text = ""
            if is_pdf:
                extracted_text = parser.extract_text_from_pdf(file)
            elif is_docx:
                extracted_text = parser.extract_text_from_docx(file)
                
            if not extracted_text:
                raise ValueError("Could not extract text")
                
        except Exception as e:
                return Response(
                {"message": f"Error parsing file: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Extract details using parser logic
        details = parser.extract_details(extracted_text)
        
        # Fallback to AI prediction for role
        if not details["role"]:
            predicted_role = parser.predict_role_with_ai(extracted_text)
            if predicted_role:
                details["role"] = predicted_role
                
        # Basic Email Extraction
        import re
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', extracted_text)
        if email_match:
            details["email"] = email_match.group(0)
        else:
            details["email"] = ""
            
        # Extract Skills
        try:
            from .services.skill_extractor import SkillExtractor
            extractor = SkillExtractor()
            skills_data = extractor.extract_skills(extracted_text)
            details["skills"] = [s["name"] for s in skills_data]
        except Exception as e:
            print(f"Error extracting skills in analyze_cv: {e}")
            details["skills"] = []
            
        return Response(details)

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
        if not (file.name.lower().endswith(".pdf") or file.name.lower().endswith(".docx")):
            return Response(
                {"message": "Only PDF and DOCX files are supported"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate File Content
        parser = CVParser()
        is_pdf = parser.is_valid_pdf(file)
        is_docx = parser.is_valid_docx(file)
        
        if not (is_pdf or is_docx):
            return Response(
                {"message": "Invalid file content"},
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
                cv.refresh_from_db()
                with cv.file.open("rb") as f:
                    file_content = f.read()
                    f.seek(0)
                    
                    # Determine type again or store it - simpler to re-check or check extension
                    # Since we validated on upload, we can check byte signature or just try both
                    # Or check extension from file name if available
                    
                    extracted_text = None
                    if cv.file.name.lower().endswith('.pdf') and parser.is_valid_pdf(f):
                        f.seek(0)
                        extracted_text = parser.extract_text_from_pdf(f)
                    elif cv.file.name.lower().endswith('.docx'):
                        # is_valid_docx checks but we can just try extract
                        f.seek(0)
                        extracted_text = parser.extract_text_from_docx(f)
                    else:
                        # Fallback try both
                        f.seek(0)
                        if parser.is_valid_pdf(f):
                            f.seek(0)
                            extracted_text = parser.extract_text_from_pdf(f)
                        else:
                            f.seek(0)
                            extracted_text = parser.extract_text_from_docx(f)

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
                        Skill.objects.update_or_create(
                            employee=employee,
                            name=skill_name,
                            defaults={
                                "source": "CV",
                                "confidence_score": skill_data["confidence_score"]
                            }
                        )
                    
                    # Extract and update details
                    details = parser.extract_details(extracted_text)
                    
                    # Fallback to AI prediction for role if heuristic failed
                    if not details["role"]:
                        predicted_role = parser.predict_role_with_ai(extracted_text)
                        if predicted_role:
                            details["role"] = predicted_role
                    
                    # Update Title if found
                    if details["role"] and (not employee.title or employee.title.startswith("New Employee")):
                        employee.title = details["role"]
                        employee.save()
                    
                    # Update Name if found
                    if details["name"]:
                        user = employee.user
                        current_name = f"{user.first_name} {user.last_name}".strip()
                        # Only update if name looks generic or is just email
                        if not current_name or "@" in current_name or current_name.lower().startswith("new user"):
                            name_parts = details["name"].split()
                            user.first_name = name_parts[0]
                            user.last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
                            user.save()

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
            status__in=["ASSIGNED", "IN_PROGRESS", "BLOCKED"]
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
        else:
            # PMs see only tasks they created
            queryset = queryset.filter(created_by=user)

        return queryset.order_by("-created_at")

    def create(self, request, *args, **kwargs):
        """Create task and return matches."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Get the created task instance
        task = serializer.instance
        
        # Calculate matches
        engine = MatchingEngine()
        matches = engine.find_best_matches(task, limit=5, min_score=40.0)
        
        # Serialize response
        response_data = serializer.data
        response_data["matches"] = matches
        
        headers = self.get_success_headers(serializer.data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        """Create task with current user as creator."""
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=["post"], url_path="analyze")
    def analyze_document(self, request):
        """Analyze uploaded document to extract task details."""
        if "file" not in request.FILES:
            return Response(
                {"message": "No file provided"},
                status=status.HTTP_400_BAD_REQUEST
            )

        file = request.FILES["file"]
        
        # Parse PDF
        # Parse Document
        parser = CVParser() # Valid for generic docs too
        
        is_pdf = parser.is_valid_pdf(file)
        is_docx = parser.is_valid_docx(file)
        
        extracted_text = None
        
        if is_pdf:
             extracted_text = parser.extract_text_from_pdf(file)
        elif is_docx:
             extracted_text = parser.extract_text_from_docx(file)
        else:
             return Response(
                {"message": "Only PDF and DOCX files are supported"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if not extracted_text:
             return Response(
                {"message": "Could not extract text from document"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Extract details
        details = parser.extract_task_details(extracted_text)
        
        # Extract Skills using SkillExtractor
        extractor = SkillExtractor()
        skills_data = extractor.extract_skills(extracted_text)
        details["requiredSkills"] = [
            extractor.normalize_skill_name(s["name"]) for s in skills_data
        ]
        
        return Response(details)

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

        active_statuses = ["ASSIGNED", "IN_PROGRESS", "BLOCKED"]

        with transaction.atomic():
            TaskAssignment.objects.filter(
                task=task,
                status__in=active_statuses
            ).exclude(employee=employee).update(status="CANCELLED")

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
                # If reactivating an old assignment (or even if already active),
                # update the timestamp so it appears as the most recent.
                assignment.status = "ASSIGNED"
                assignment.assigned_at = timezone.now()
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
                status__in=["ASSIGNED", "IN_PROGRESS", "BLOCKED"]
            ).count()

            capacity = employee.current_workload

            data = {
                "active_tasks": active_tasks,
                "unassigned_tasks": 0,
                "employee_capacity": round(capacity, 1),
                "skills_coverage": 0
            }
        else:
            # Filter stats by PM's data
            active_tasks = Task.objects.filter(
                created_by=user,
                status__in=["ASSIGNED", "IN_PROGRESS", "BLOCKED"]
            ).count()

            unassigned_tasks = Task.objects.filter(
                created_by=user,
                status="UNASSIGNED"
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
                "skills_coverage": round(skills_coverage, 1)
            }

        serializer = DashboardStatsSerializer(data)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def debug_media(request):
    """Debug view to check media file existence."""
    from django.conf import settings
    import os
    
    media_root = settings.MEDIA_ROOT
    media_url = settings.MEDIA_URL
    path = request.GET.get('path', '')
    
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
            cvs_path = os.path.join(media_root, 'cvs')
            if os.path.exists(cvs_path):
                folder_contents.extend([f"cvs/{f}" for f in os.listdir(cvs_path)])
        else:
            folder_contents = ["Media Root does not exist"]
    except Exception as e:
        folder_contents = [str(e)]

    return Response({
        "MEDIA_ROOT": media_root,
        "MEDIA_URL": media_url,
        "Requested Path": path,
        "Full Path": full_path,
        "Exists": exists,
        "Folder Contents": folder_contents,
        "DEBUG": settings.DEBUG,
        "Service": "ITAS Backend API"
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def debug_email(request):
    """Debug view to test email sending."""
    from django.core.mail import send_mail
    from django.conf import settings
    
    recipient = request.GET.get('recipient')
    if not recipient:
        return Response(
            {"message": "Please provide 'recipient' query parameter"},
            status=status.HTTP_400_BAD_REQUEST
        )
        
    try:
        send_mail(
             "Debug Email Test",
             f"This is a test email sent from {settings.EMAIL_HOST}",
             settings.DEFAULT_FROM_EMAIL,
             [recipient],
             fail_silently=False,
        )
        return Response ({
            "status": "SUCCESS", 
            "message": f"Email sent to {recipient}",
            "config": {
                "HOST": settings.EMAIL_HOST,
                "PORT": settings.EMAIL_PORT,
                "USER": settings.EMAIL_HOST_USER[:3] + "***" if settings.EMAIL_HOST_USER else "NOT SET",
                "TLS": settings.EMAIL_USE_TLS
            }
        })
    except Exception as e:
        return Response({
            "status": "FAILED", 
            "error": str(e),
            "config": {
                 "HOST": settings.EMAIL_HOST,
                 "PORT": settings.EMAIL_PORT,
                 "USER": settings.EMAIL_HOST_USER[:3] + "***" if settings.EMAIL_HOST_USER else "NOT SET",
                 "TLS": settings.EMAIL_USE_TLS
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
