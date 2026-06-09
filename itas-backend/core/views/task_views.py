from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import viewsets, status, exceptions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate, get_user_model
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from core.models import User, Employee, Project, Task, TaskAssignment, TaskSkillEvaluation, Skill, AuditLog, CV
from core.serializers import UserSerializer, EmployeeSerializer, ProjectSerializer, TaskSerializer, TaskAssignmentSerializer, TaskMatchSerializer
from core.services.audit_service import AuditService
from core.services.matching_engine import MatchingEngine
from core.services.cv_parser import CVParser
from core.services.skill_extractor import SkillExtractor


class TaskViewSet(viewsets.ModelViewSet):
    """Task endpoints."""

    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    pagination_class = None  # Disable pagination for now, return all results

    def get_queryset(self):
        """Filter tasks based on user role."""
        user = self.request.user
        queryset = Task.objects.select_related(
            "created_by", "project"
        ).prefetch_related("task_skills")

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

        AuditService.log(request.user, "CREATE", serializer.instance, "Created task")

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
                {"message": "No file provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        file = request.FILES["file"]

        # Parse PDF
        # Parse Document
        parser = CVParser()  # Valid for generic docs too

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
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not extracted_text:
            return Response(
                {"message": "Could not extract text from document"},
                status=status.HTTP_400_BAD_REQUEST,
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
        
        from django.core.cache import cache
        from django.conf import settings
        
        cached_matches = cache.get(f"task_matches_{task.id}")
        if cached_matches:
            return Response(cached_matches)

        engine = MatchingEngine()
        rule_based_results = engine.find_best_matches(task, limit=10, min_score=50.0)
        
        try:
            from apps.ai.services.recommendation_service import RecommendationService
            ml_results = RecommendationService().get_recommendations(task, limit=10)
        except Exception as e:
            print(f"Error calling RecommendationService: {e}")
            ml_results = []
            
        if settings.SHADOW_ML_DEPLOYMENT:
            print(f"SHADOW_ML_DEPLOYMENT: ML Results would have been: {ml_results}")
            serializer = TaskMatchSerializer(rule_based_results, many=True)
            result_data = serializer.data
        else:
            if not ml_results:
                serializer = TaskMatchSerializer(rule_based_results, many=True)
                result_data = serializer.data
            else:
                # Merge results: if ml_results is non-empty, blend scores:
                # For each candidate, final_score = (rule_score * 0.6) + (ml_score * 0.4)
                rule_dict = {m['employee_id']: m['suitability_score'] for m in rule_based_results}
                merged_results = []
                for ml_match in ml_results:
                    emp_id = ml_match['employee_id']
                    rule_score = rule_dict.get(emp_id, 0.0)
                    ml_score = ml_match['prediction_score']
                    final_score = (rule_score * 0.6) + (ml_score * 0.4)
                    ml_match['suitability_score'] = final_score
                    merged_results.append(ml_match)
                    
                # Add employees that only appear in rule_based
                ml_emp_ids = {m['employee_id'] for m in ml_results}
                for r in rule_based_results:
                    if r['employee_id'] not in ml_emp_ids:
                        # ml_score is 0 for them
                        final_score = r['suitability_score'] * 0.6
                        r['suitability_score'] = final_score
                        merged_results.append(r)
                        
                # Sort by final_score descending
                merged_results.sort(key=lambda x: x['suitability_score'], reverse=True)
                # Take top 10
                merged_results = merged_results[:10]
                result_data = merged_results
                
        # Cache for next time
        cache.set(f"task_matches_{task.id}", result_data, timeout=3600)
        
        return Response(result_data)

    @action(detail=True, methods=["post"], url_path="assign")
    def assign_task(self, request, pk=None):
        """Assign task to an employee."""
        task = self.get_object()
        employee_id = request.data.get("employee_id")

        if not employee_id:
            return Response(
                {"message": "employee_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response(
                {"message": "Employee not found"}, status=status.HTTP_404_NOT_FOUND
            )

        engine = MatchingEngine()
        score = engine.calculate_suitability_score(employee, task, task.required_skills)

        active_statuses = ["ASSIGNED", "IN_PROGRESS", "BLOCKED"]

        with transaction.atomic():
            TaskAssignment.objects.filter(
                task=task, status__in=active_statuses
            ).exclude(employee=employee).update(status="CANCELLED")

            assignment, created = TaskAssignment.objects.get_or_create(
                task=task,
                employee=employee,
                defaults={"suitability_score": score, "status": "ASSIGNED"},
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

        AuditService.log(
            request.user,
            "ASSIGN",
            task,
            f"Assigned to {employee.name} with score {score}",
        )

        serializer = TaskAssignmentSerializer(assignment)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="unassign")
    def unassign_task(self, request, pk=None):
        """Unassign task from current employee."""
        task = self.get_object()

        with transaction.atomic():
            TaskAssignment.objects.filter(
                task=task, status__in=["ASSIGNED", "IN_PROGRESS", "BLOCKED"]
            ).update(status="CANCELLED")

            task.status = "UNASSIGNED"
            task.save()

        AuditService.log(request.user, "UPDATE", task, "Unassigned task")

        return Response({"message": "Task unassigned successfully"})

    @action(detail=True, methods=["post"], url_path="progress")
    def update_progress(self, request, pk=None):
        """Update task progress (Status and Notes) for Employee."""
        task = self.get_object()
        user = request.user

        # Find assignment for this user
        try:
            employee = user.employee_profile
            assignment = TaskAssignment.objects.get(task=task, employee=employee)
        except (AttributeError, TaskAssignment.DoesNotExist):
            return Response(
                {"message": "You are not assigned to this task"},
                status=status.HTTP_403_FORBIDDEN,
            )

        new_status = request.data.get("status")
        notes = request.data.get("notes")

        if new_status:
            # Update assignment status
            assignment.status = new_status

            # Sync to Task status if needed (simplified logic)
            if new_status == "COMPLETED":
                task.status = "COMPLETED"
                assignment.completed_at = timezone.now()
            elif new_status == "IN_PROGRESS":
                task.status = "IN_PROGRESS"
                if not assignment.started_at:
                    assignment.started_at = timezone.now()

            task.save()

        if notes is not None:
            assignment.notes = notes

        assignment.save()

        AuditService.log(user, "UPDATE", task, f"Updated progress: {new_status}")

        return Response({"message": "Progress updated"})

    @action(detail=True, methods=["post"], url_path="rate-performance")
    def rate_performance(self, request, pk=None):
        """Rate employee performance with detailed metrics for a completed task (PM only)."""
        task = self.get_object()
        user = request.user

        if user.role != "PM":
            return Response(
                {"message": "Only Project Managers can rate performance"},
                status=status.HTTP_403_FORBIDDEN,
            )

        data = request.data

        try:
            quality = int(data.get("quality_rating", 0))
            timeliness = int(data.get("timeliness_rating", 0))
            communication = int(data.get("communication_rating", 0))
            technical = int(data.get("technical_rating", 0))

            for r in [quality, timeliness, communication, technical]:
                if r < 1 or r > 5:
                    raise ValueError("Ratings must be between 1 and 5")

        except (TypeError, ValueError) as e:
            return Response(
                {
                    "message": (
                        str(e)
                        if str(e)
                        else "Ratings must be valid integers between 1 and 5"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        comments = data.get("performance_comments", "")
        overall_rating = (quality + timeliness + communication + technical) / 4.0

        # Find the most recent active/completed assignment
        assignment = (
            TaskAssignment.objects.filter(task=task).order_by("-assigned_at").first()
        )
        if not assignment:
            return Response(
                {"message": "No assignment found for this task"},
                status=status.HTTP_404_NOT_FOUND,
            )

        assignment.quality_rating = quality
        assignment.timeliness_rating = timeliness
        assignment.communication_rating = communication
        assignment.technical_rating = technical
        assignment.performance_comments = comments
        assignment.performance_rating = overall_rating
        assignment.save()
        
        skill_evaluations = data.get("skill_evaluations", [])
        if skill_evaluations:
            with transaction.atomic():
                assignment.skill_evaluations.all().delete()
                for eval_data in skill_evaluations:
                    TaskSkillEvaluation.objects.create(
                        assignment=assignment,
                        skill_name=eval_data.get("skill_name", "Unknown"),
                        required_level=int(eval_data.get("required_level", 3)),
                        achieved_level=int(eval_data.get("achieved_level", 3)),
                        pm_comment=eval_data.get("pm_comment", "")
                    )

        AuditService.log(
            user, "UPDATE", task, f"Rated performance detailed: {overall_rating}/5"
        )

        return Response(
            {
                "message": "Performance rating saved successfully",
                "performance_rating": overall_rating,
            }
        )

