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
        
        extracted_text = None
        if cv.file.name.lower().endswith(".pdf"):
            extracted_text = parser.extract_text_from_pdf(cv.file.path)
        elif cv.file.name.lower().endswith(".docx"):
            extracted_text = parser.extract_text_from_docx(cv.file.path)
            
        cv.extracted_text = extracted_text or ''
        cv.status = "READY"
        cv.save()
        
        if extracted_text:
            from core.services.skill_extractor import SkillExtractor
            from core.models import Skill
            from django.db import transaction
            import re
            
            extractor = SkillExtractor()
            cleaned_text = extracted_text
            if re.search(r"\b([A-Za-z]\s){2,}[A-Za-z]\b", cleaned_text):
                cleaned_text = re.sub(r"([A-Za-z])\s(?=[A-Za-z]\b)", r"\1", cleaned_text)
            cleaned_text = re.sub(r"\b([A-Za-z])\s([A-Za-z]{3,})\b", r"\1\2", cleaned_text)

            skills_data = extractor.extract_skills(cleaned_text)

            with transaction.atomic():
                Skill.objects.filter(employee=cv.employee, source="CV").delete()
                for skill_data in skills_data:
                    skill_name = extractor.normalize_skill_name(skill_data["name"])
                    Skill.objects.update_or_create(
                        employee=cv.employee,
                        name=skill_name,
                        defaults={
                            "source": "CV",
                            "confidence_score": skill_data["confidence_score"],
                        },
                    )

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

@shared_task
def refresh_recommendations_async(task_id):
    """Placeholder to recalculate rankings for a task asynchronously."""
    try:
        task = Task.objects.get(id=task_id)
        # Re-compute recommendations using matching engine
        from core.services.matching_engine import MatchingEngine
        engine = MatchingEngine()
        # the engine caches or stores the result
        return True
    except Exception as e:
        return False
