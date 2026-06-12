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


class EmployeeViewSet(viewsets.ModelViewSet):
    """Employee endpoints."""

    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer

    def get_queryset(self):
        """Filter employees based on user role."""
        user = self.request.user
        queryset = Employee.objects.select_related("user", "manager").prefetch_related(
            "skill_set"
        )

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

        # Apply optional filters
        team = self.request.query_params.get("team")
        role = self.request.query_params.get("role")
        title = self.request.query_params.get("title")

        if team:
            queryset = queryset.filter(team__icontains=team)
        if role:
            queryset = queryset.filter(role__icontains=role)
        if title:
            queryset = queryset.filter(title__icontains=title)

        return queryset

    def create(self, request, *args, **kwargs):
        """Create new employee and associated user."""
        # Check permissions (only PM can create employees)
        if request.user.role != "PM":
            return Response(
                {"message": "Only Project Managers can add employees"},
                status=status.HTTP_403_FORBIDDEN,
            )

        data = request.data
        email = data.get("email")
        name = data.get("name")
        title = data.get("title")

        if not email or not name:
            return Response(
                {"message": "Email and name are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if user exists
        if User.objects.filter(email=email).exists():
            return Response(
                {"message": "User with this email already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                # Create User
                username = email.split("@")[0]
                # Ensure unique username
                if User.objects.filter(username=username).exists():
                    import uuid

                    username = f"{username}_{uuid.uuid4().hex[:4]}"

                import secrets
                import string

                random_password = "".join(
                    secrets.choice(string.ascii_letters + string.digits)
                    for _ in range(12)
                )
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=random_password,
                    first_name=name.split(" ")[0],
                    last_name=" ".join(name.split(" ")[1:]) if " " in name else "",
                    role="EMPLOYEE",
                )

                # Create Employee
                employee = Employee.objects.create(
                    user=user,
                    manager=request.user,  # Assign current PM as manager
                    title=title,
                    email=email,
                )

                # Add initial skills if provided
                skills = data.get("skills", [])
                if skills and isinstance(skills, list):
                    for skill_name in skills:
                        Skill.objects.create(
                            employee=employee,
                            name=skill_name,
                            source="MANUAL",  # Created via form (even if auto-filled)
                            confidence_score=1.0,
                        )

                serializer = self.get_serializer(employee)
                AuditService.log(
                    request.user, "CREATE", employee, f"Created employee {email}"
                )
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def perform_destroy(self, instance):
        """Delete employee and associated user."""
        if self.request.user.role != "PM":
            raise exceptions.PermissionDenied(
                "Only Project Managers can remove employees."
            )

        user = instance.user
        instance.delete()
        AuditService.log(
            self.request.user, "DELETE", instance, f"Deleted employee {user.email}"
        )
        user.delete()

    @action(detail=False, methods=["post"], url_path="analyze")
    def analyze_cv(self, request):
        """
        Analyze a CV file and return extracted details (Name, Email, Title)
        for pre-filling the employee creation form.
        """
        if "file" not in request.FILES:
            return Response(
                {"message": "No file provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        file = request.FILES["file"]

        # Parse PDF
        parser = CVParser()
        is_pdf = parser.is_valid_pdf(file)
        is_docx = parser.is_valid_docx(file)

        if not (is_pdf or is_docx):
            return Response(
                {"message": "Only PDF and DOCX files are supported"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Read file
        if hasattr(file, "read"):
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
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Extract details using parser logic
        details = parser.extract_details(extracted_text)

        # Fallback to AI prediction for title
        if not details.get("title"):
            predicted_title = parser.predict_role_with_ai(extracted_text)
            if predicted_title:
                details["title"] = predicted_title

        # Basic Email Extraction
        import re

        email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", extracted_text)
        if email_match:
            details["email"] = email_match.group(0)
        else:
            details["email"] = ""

        # Extract Skills
        try:
            extractor = SkillExtractor()
            
            import re
            cleaned_text = extracted_text
            if re.search(r"\b([A-Za-z]\s){2,}[A-Za-z]\b", cleaned_text):
                cleaned_text = re.sub(r"([A-Za-z])\s(?=[A-Za-z]\b)", r"\1", cleaned_text)
            cleaned_text = re.sub(r"\b([A-Za-z])\s([A-Za-z]{3,})\b", r"\1\2", cleaned_text)

            skills_data = extractor.extract_skills(cleaned_text)
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
                {"message": "No file provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        file = request.FILES["file"]

        # Validate file type
        if not (
            file.name.lower().endswith(".pdf") or file.name.lower().endswith(".docx")
        ):
            return Response(
                {"message": "Only PDF and DOCX files are supported"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate File Content
        parser = CVParser()
        is_pdf = parser.is_valid_pdf(file)
        is_docx = parser.is_valid_docx(file)

        if not (is_pdf or is_docx):
            return Response(
                {"message": "Invalid file content"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Create or update CV record
        cv, created = CV.objects.get_or_create(employee=employee)
        cv.file = file
        cv.status = "PROCESSING"
        cv.error_message = None
        cv.save()

        # Process CV in background celery task
        from core.tasks import parse_cv_async
        parse_cv_async.delay(cv.id)

        return Response(
            {"message": "CV uploaded and processing started", "status": "PROCESSING"}
        )

    @action(detail=False, methods=["get"], url_path="my-profile")
    def get_my_profile(self, request):
        """Get current employee's profile and tasks."""
        user = request.user

        if user.role != "EMPLOYEE":
            return Response(
                {"message": "This endpoint is only for employees"},
                status=status.HTTP_403_FORBIDDEN,
            )

        employee = getattr(user, "employee_profile", None)
        if not employee:
            return Response(
                {"message": "Employee profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        employee_data = EmployeeSerializer(employee).data

        active_assignments = TaskAssignment.objects.filter(
            employee=employee, status__in=["ASSIGNED", "IN_PROGRESS", "BLOCKED"]
        ).select_related("task")

        completed_assignments = TaskAssignment.objects.filter(
            employee=employee, status="COMPLETED"
        ).select_related("task").order_by("-completed_at")[:5]

        tasks_data = []
        for assignment in list(active_assignments) + list(completed_assignments):
            task = assignment.task
            tasks_data.append(
                {
                    "id": str(task.id),
                    "title": task.title,
                    "description": task.description,
                    "status": assignment.status,
                    "priority": task.priority,
                    "suitability_score": assignment.suitability_score,
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                }
            )

        return Response(
            {
                "employee": employee_data,
                "tasks": tasks_data,
                "workload": employee.current_workload,
            }
        )

    @action(detail=True, methods=["get"], url_path="performance-profile")
    def get_performance_profile(self, request, pk=None):
        """Get employee's detailed performance history and aggregated metrics."""
        employee = self.get_object()
        
        completed_assignments = TaskAssignment.objects.filter(
            employee=employee, status="COMPLETED"
        ).select_related("task", "task__project").prefetch_related("skill_evaluations").order_by("completed_at")
        
        history = []
        skill_scores = {}
        total_rating = 0
        rated_tasks_count = 0
        
        for a in completed_assignments:
            task = a.task
            
            for eval in a.skill_evaluations.all():
                key = eval.skill_name.lower().strip()
                if key not in skill_scores:
                    skill_scores[key] = {
                        "name": eval.skill_name,
                        "scores": []
                    }
                skill_scores[key]["scores"].append(eval.achieved_level)
                
            if a.performance_rating:
                total_rating += a.performance_rating
                rated_tasks_count += 1
                
            history.append({
                "assignment_id": str(a.id),
                "task_id": str(task.id),
                "task_title": task.title,
                "task_description": task.description,
                "project_name": task.project.title if task.project else None,
                "start_date": task.start_date.isoformat() if task.start_date else None,
                "end_date": a.completed_at.isoformat() if a.completed_at else None,
                "task_type": getattr(task, "task_type", None),
                "complexity_level": getattr(task, "complexity_level", None),
                "performance_rating": a.performance_rating,
                "pm_comments": a.performance_comments,
                "skill_evaluations": [
                    {
                        "skill_name": eval.skill_name,
                        "required_level": eval.required_level,
                        "achieved_level": eval.achieved_level,
                        "pm_comment": eval.pm_comment
                    } for eval in a.skill_evaluations.all()
                ]
            })
            
        # Get base static skills
        base_skills = {}
        for skill in employee.skill_set.all():
            confidence = max(0.0, min(1.0, skill.confidence_score or 0.0))
            if getattr(skill, "source", None) == "MANUAL":
                confidence = max(confidence, 0.9)
            base_skills[skill.name.lower().strip()] = {
                "name": skill.name,
                "score": max(1.0, confidence * 5.0)
            }

        weighted_average_skill_score_per_skill = {}
        for key, data in base_skills.items():
            weighted_average_skill_score_per_skill[data["name"]] = data["score"]
            
        for key, data in skill_scores.items():
            weighted_average_skill_score_per_skill[data["name"]] = sum(data["scores"])/len(data["scores"])
            
        skill_analytics = []
        for key, data in base_skills.items():
            if key in skill_scores:
                scores = skill_scores[key]["scores"]
                skill_analytics.append({
                    "skill_name": data["name"],
                    "score": round(sum(scores)/len(scores), 1),
                    "tasks_used": len(scores)
                })
            else:
                skill_analytics.append({
                    "skill_name": data["name"],
                    "score": round(data["score"], 1),
                    "tasks_used": 0
                })
                
        for key, data in skill_scores.items():
            if key not in base_skills:
                scores = data["scores"]
                skill_analytics.append({
                    "skill_name": data["name"],
                    "score": round(sum(scores)/len(scores), 1),
                    "tasks_used": len(scores)
                })
                
        skill_analytics.sort(key=lambda x: (x["tasks_used"], x["score"]), reverse=True)
        
        # Skill progression over time
        skill_progression = {}
        for key, data in skill_scores.items():
            scores = data["scores"]
            name = data["name"]
            if len(scores) > 1:
                trend = "IMPROVING" if scores[-1] > scores[0] else "DECLINING" if scores[-1] < scores[0] else "STABLE"
            else:
                trend = "INSUFFICIENT_DATA"
            skill_progression[name] = trend
            
        # Consistency score (variance)
        consistency_score = 100
        if rated_tasks_count > 1:
            avg_rating = total_rating / rated_tasks_count
            variance = sum((a.performance_rating - avg_rating) ** 2 for a in completed_assignments if a.performance_rating) / rated_tasks_count
            # scale variance (0-25) into a 0-100 score where lower variance = higher consistency
            consistency_score = max(0, 100 - (variance * 20))
            
        reliability_index = 0
        total_assigned = TaskAssignment.objects.filter(employee=employee).count()
        if rated_tasks_count > 0 and total_assigned > 0:
            avg_rating = total_rating / rated_tasks_count
            completion_rate = completed_assignments.count() / total_assigned
            reliability_index = (avg_rating / 5.0) * completion_rate * 100
            
        return Response({
            "employee_id": str(employee.id),
            "employee_name": employee.name,
            "metrics": {
                "weighted_average_skill_score": weighted_average_skill_score_per_skill,
                "skill_analytics": skill_analytics,
                "skill_progression": skill_progression,
                "consistency_score": round(consistency_score, 2),
                "reliability_index": round(reliability_index, 2),
                "total_completed_tasks": completed_assignments.count(),
                "rated_tasks_count": rated_tasks_count,
            },
            "task_history": history
        })

