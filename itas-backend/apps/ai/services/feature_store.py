from typing import List
import pandas as pd
from core.models import Task, Employee

class FeatureStore:
    """
    Computes and structures features for ML inference and training.
    """
    
    def __init__(self):
        from .embedding_service import EmbeddingService
        self.embedding_service = EmbeddingService()

    def build_features(self, task: Task, candidates: List[Employee]) -> pd.DataFrame:
        """
        Builds a DataFrame of features for a task and candidate list.
        """
        features_list = []
        task_skills = set(task.required_skills)
        
        for emp in candidates:
            emp_skills = set(emp.skills)
            
            # 1. Skill Features
            overlap = len(emp_skills.intersection(task_skills))
            skill_overlap_ratio = overlap / len(task_skills) if task_skills else 1.0
            missing_skills = len(task_skills - emp_skills)
            
            # 2. Performance Features
            avg_rating = emp.average_performance or 3.0
            
            # 3. Workload
            workload = emp.current_workload
            availability = 1.0 - (workload / 100.0)
            
            # 4. Semantic Match
            semantic_score = self.embedding_service.calculate_similarity(task, emp)
            
            # Construct row
            row = {
                "skill_overlap_ratio": skill_overlap_ratio,
                "missing_required_skills": missing_skills,
                "average_rating": avg_rating,
                "current_workload_pct": workload / 100.0,
                "availability_score": availability,
                "semantic_match_score": semantic_score,
                "task_priority_encoded": self._encode_priority(task.priority),
                "task_complexity_encoded": self._encode_complexity(task.complexity_level)
            }
            features_list.append(row)
            
        return pd.DataFrame(features_list)
        
    def _encode_priority(self, priority: str) -> int:
        mapping = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
        return mapping.get(priority, 2)
        
    def _encode_complexity(self, comp: str) -> int:
        mapping = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        return mapping.get(comp, 2)
