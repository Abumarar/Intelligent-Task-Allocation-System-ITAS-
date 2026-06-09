from core.models import Task, Employee

class EmbeddingService:
    """Wrapper for sentence-transformers to calculate semantic matches."""
    
    def calculate_similarity(self, task: Task, employee: Employee) -> float:
        # For now, falls back to the existing ML pipeline until new model is trained
        from core.services.ml.inference_pipeline import InferencePipeline
        pipeline = InferencePipeline()
        
        task_text = f"{task.title} {task.description or ''}"
        emp_text = ""
        if hasattr(employee, 'cv') and employee.cv and employee.cv.extracted_text:
            emp_text = employee.cv.extracted_text
            
        if not task_text or not emp_text:
            return 0.0
            
        return pipeline.calculate_similarity(task_text, emp_text)
