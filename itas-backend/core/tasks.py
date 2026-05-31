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
        cv.save()
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
