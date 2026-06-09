from typing import List, Dict, Any
from core.models import Task, Employee

class RecommendationService:
    """
    ML-powered recommendation service replacing the rule-based MatchingEngine.
    """
    
    def __init__(self):
        from .feature_store import FeatureStore
        from apps.ai.inference.predictor import RankerPredictor
        
        self.feature_store = FeatureStore()
        self.predictor = RankerPredictor()

    def get_recommendations(self, task: Task, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get ranked candidate recommendations for a task using the ML model.
        """
        # 1. Fetch Candidates (Pre-filter to exclude fully booked)
        candidates = self._fetch_candidates()
        
        if not candidates:
            return []
            
        # 2. Extract Features
        features_df = self.feature_store.build_features(task, candidates)
        
        # 3. Predict & Rank
        predictions = self.predictor.predict(features_df)
        
        # 4. Format Output
        results = []
        for i, emp in enumerate(candidates):
            score = float(predictions[i])
            results.append({
                "employee_id": emp.id,
                "employee_name": emp.name,
                "employee_title": emp.title,
                "ml_score": round(score, 2),
                "features": features_df.iloc[i].to_dict() if features_df is not None else {}
            })
            
        results.sort(key=lambda x: x["ml_score"], reverse=True)
        return results[:limit]
        
    def _fetch_candidates(self) -> List[Employee]:
        """Fetch available employees from DB."""
        # Pre-filtering logic similar to old matching_engine
        from django.db.models import Count, Q
        
        from django.conf import settings
        MAX_CAPACITY = settings.EMPLOYEE_MAX_CAPACITY
        employees_query = Employee.objects.select_related("user").prefetch_related("skill_set")
        employees_query = employees_query.annotate(
            active_task_count=Count(
                "taskassignment_set",
                filter=Q(taskassignment_set__status__in=["ASSIGNED", "IN_PROGRESS", "BLOCKED"]),
            )
        ).filter(active_task_count__lt=MAX_CAPACITY)
        
        return list(employees_query)
