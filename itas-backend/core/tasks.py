from celery import shared_task
from core.models import CV, Employee, Task
from core.services.cv_parser import CVParser
from core.services.ml.feature_transformer import FeatureTransformer

@shared_task
def parse_cv_async(cv_id):
    try:
        cv = CV.objects.get(id=cv_id)
        cv.status = "PROCESSING"
        cv.save()
        
        parser = CVParser()
        result = parser.parse_cv(cv.file.path)
        
        cv.extracted_text = result.get('text', '')
        cv.status = "READY"
        
        from django.utils import timezone
        cv.processed_at = timezone.now()
        cv.save()
        
        from core.services.skill_extractor import SkillExtractor
        from core.models import Skill
        from django.db import transaction
        
        extractor = SkillExtractor()
        skills_data = extractor.extract_skills(cv.extracted_text)
        employee = cv.employee

        with transaction.atomic():
            Skill.objects.filter(employee=employee, source="CV").delete()

            for skill_data in skills_data:
                skill_name = extractor.normalize_skill_name(skill_data["name"])
                Skill.objects.update_or_create(
                    employee=employee,
                    name=skill_name,
                    defaults={
                        "source": "CV",
                        "confidence_score": skill_data["confidence_score"],
                    },
                )

            # Extract and update details
            details = parser.extract_details(cv.extracted_text)

            # Fallback to AI prediction for role if heuristic failed
            if not details["role"]:
                predicted_role = parser.predict_role_with_ai(cv.extracted_text)
                if predicted_role:
                    details["role"] = predicted_role

            # Update Title if found
            if details["role"] and (
                not employee.title or employee.title.startswith("New Employee")
            ):
                employee.title = details["role"]
                employee.save()

            # Update Name if found
            if details["name"]:
                user = employee.user
                current_name = f"{user.first_name} {user.last_name}".strip()
                # Only update if name looks generic or is just email
                if (
                    not current_name
                    or "@" in current_name
                    or current_name.lower().startswith("new user")
                ):
                    name_parts = details["name"].split()
                    user.first_name = name_parts[0]
                    user.last_name = (
                        " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
                    )
                    user.save()

        generate_embeddings_async.delay(cv.employee_id)
        return True
    except Exception as e:
        if 'cv' in locals():
            cv.status = "FAILED"
            cv.error_message = str(e)
            cv.save()
        return False

@shared_task
def generate_embeddings_async(employee_id):
    try:
        employee = Employee.objects.get(id=employee_id)
        if not hasattr(employee, 'cv') or not employee.cv.extracted_text:
            return False
            
        transformer = FeatureTransformer()
        embedding = transformer.transform_text_to_embedding(employee.cv.extracted_text)
        return True
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return False

from django.core.cache import cache

@shared_task
def refresh_recommendations_async(task_id):
    """Compute matches and cache them in Django's cache framework."""
    try:
        task = Task.objects.get(id=task_id)
        from core.services.matching_engine import MatchingEngine
        engine = MatchingEngine()
        matches = engine.find_best_matches(task, limit=10)
        cache_key = f"task_matches_{task_id}"
        cache.set(cache_key, matches, timeout=3600)  # 1 hour TTL
        return True
    except Exception as e:
        return False

@shared_task
def send_assignment_email_async(employee_id, task_id):
    from core.models import Employee, Task
    from core.services.email_service import EmailService
    employee = Employee.objects.get(id=employee_id)
    task = Task.objects.get(id=task_id)
    EmailService.send_task_assignment_email(employee, task)

@shared_task
def send_completion_email_async(user_id, task_id):
    from core.models import Task
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.get(id=user_id)
    task = Task.objects.get(id=task_id)
    EmailService.send_task_completion_email(user, task)
