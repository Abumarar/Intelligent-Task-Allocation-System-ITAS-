"""
Matching Engine for Task-Employee Suitability Scoring
Calculates how well an employee matches task requirements based on skills, workload, and other factors.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from django.db.models import Case, Count, F, Q, Value, When
from django.db.models.functions import Lower

from core.models import Employee, Task
from core.services.skill_extractor import SkillExtractor


class MatchingEngine:
    """Service for calculating task-employee suitability scores."""

    def __init__(self):
        self.weights_by_priority = {
            "HIGH": {
                "skill": 0.5,
                "coverage": 0.15,
                "experience": 0.15,
                "workload": 0.1,
                "performance": 0.1,
            },
            "MEDIUM": {
                "skill": 0.45,
                "coverage": 0.15,
                "experience": 0.1,
                "workload": 0.2,
                "performance": 0.1,
            },
            "LOW": {
                "skill": 0.35,
                "coverage": 0.15,
                "experience": 0.1,
                "workload": 0.3,
                "performance": 0.1,
            },
        }
        self.skill_extractor = SkillExtractor()
        
        from core.services.ml.inference_pipeline import InferencePipeline
        self.ml_pipeline = InferencePipeline()

    def calculate_suitability_score(
        self, employee: Employee, task: Task, required_skills: List[str]
    ) -> float:
        """
        Calculate suitability score (0-100) for employee-task match.

        Args:
            employee: Employee instance
            task: Task instance
            required_skills: List of required skill names

        Returns:
            Suitability score from 0 to 100
        """
        normalized_required = self._normalize_required_skills(required_skills)
        skill_profile = self._build_skill_profile(employee)
        weights = self._get_weights(task.priority)

        total_score, _ = self._calculate_total_score(
            employee, normalized_required, skill_profile, weights
        )

        return round(total_score * 100, 2)

    def _calculate_total_score(
        self,
        employee: Employee,
        normalized_required: List[str],
        skill_profile: Dict[str, float],
        weights: Dict[str, float],
    ) -> Tuple[float, Dict[str, float]]:
        performance_score = self._calculate_performance_score(employee)

        if not normalized_required:
            workload_score = self._calculate_workload_score(employee)
            workload_weight = weights.get("workload", 0.0)
            perf_weight = weights.get("performance", 0.0)
            total_weight = workload_weight + perf_weight

            breakdown = {
                "skill_match": 100.0,
                "historical_performance": round(performance_score * 100, 1),
                "workload_availability": round(workload_score * 100, 1)
            }

            if total_weight > 0:
                final_score = (
                    workload_score * workload_weight + performance_score * perf_weight
                ) / total_weight
                return final_score, breakdown
            return workload_score, breakdown

        skill_score = self._calculate_skill_match_score(
            skill_profile, normalized_required
        )
        coverage_score = self._calculate_coverage_score(
            skill_profile, normalized_required
        )
        experience_score = self._calculate_experience_score(
            skill_profile, normalized_required
        )
        workload_score = self._calculate_workload_score(employee)

        total_score = (
            skill_score * weights["skill"]
            + coverage_score * weights["coverage"]
            + experience_score * weights["experience"]
            + workload_score * weights["workload"]
            + performance_score * weights.get("performance", 0.0)
        )
        
        breakdown = {
            "skill_match": round(skill_score * 100, 1),
            "historical_performance": round(performance_score * 100, 1),
            "workload_availability": round(workload_score * 100, 1)
        }

        return max(0.0, min(1.0, total_score)), breakdown

    def _normalize_required_skills(self, required_skills: List[str]) -> List[str]:
        normalized = []
        for skill in required_skills or []:
            key = self.skill_extractor.normalize_skill_key(skill)
            if key:
                normalized.append(key)

        return list(dict.fromkeys(normalized))

    def _build_skill_profile(self, employee: Employee) -> Dict[str, float]:
        skill_profile: Dict[str, float] = {}
        for skill in employee.skill_set.all():
            key = self.skill_extractor.normalize_skill_key(skill.name)
            if not key:
                continue
            confidence = max(0.0, min(1.0, skill.confidence_score or 0.0))
            if skill.source == "MANUAL":
                confidence = max(confidence, 0.9)
            skill_profile[key] = max(skill_profile.get(key, 0.0), confidence)

        # Enhance with historical real performance from tasks
        from core.models import TaskAssignment
        import math
        from django.utils import timezone
        
        completed_assignments = TaskAssignment.objects.filter(
            employee=employee, status="COMPLETED"
        ).prefetch_related('skill_evaluations')
        
        now = timezone.now()
        
        for assignment in completed_assignments:
            days_ago = (now - assignment.completed_at).days if assignment.completed_at else 365
            # Decay factor: more recent tasks have higher weight (0.5 to 1.0)
            time_weight = max(0.5, math.exp(-days_ago / 365.0))
            
            for eval in assignment.skill_evaluations.all():
                key = self.skill_extractor.normalize_skill_key(eval.skill_name)
                if not key:
                    continue
                # 1-5 scale -> 0.2 to 1.0 confidence
                achieved_confidence = (eval.achieved_level / 5.0) * time_weight
                # Real performance overrides static CV skills
                skill_profile[key] = max(skill_profile.get(key, 0.0), achieved_confidence)

        return skill_profile

    def _calculate_skill_match_score(
        self, skill_profile: Dict[str, float], required_skills: List[str]
    ) -> float:
        if not required_skills:
            return 1.0

        scores = [self._match_skill(skill, skill_profile) for skill in required_skills]
        return sum(scores) / len(required_skills)

    def _calculate_coverage_score(
        self, skill_profile: Dict[str, float], required_skills: List[str]
    ) -> float:
        if not required_skills:
            return 1.0

        matched = sum(
            1
            for skill in required_skills
            if self._match_skill(skill, skill_profile) >= 0.5
        )
        return matched / len(required_skills)

    def _calculate_experience_score(
        self, skill_profile: Dict[str, float], required_skills: List[str]
    ) -> float:
        if not required_skills:
            return 0.5

        confidences = []
        for skill in required_skills:
            confidence = self._best_confidence_for_skill(skill, skill_profile)
            if confidence > 0.0:
                confidences.append(confidence)

        if not confidences:
            return 0.3

        return sum(confidences) / len(confidences)

    def _calculate_workload_score(self, employee: Employee) -> float:
        """Calculate workload score - higher is better (more available) (0-1)."""
        current_workload = employee.current_workload
        availability = 1.0 - (current_workload / 100.0)

        if current_workload >= 90:
            availability *= 0.7
        elif current_workload >= 80:
            availability *= 0.85

        return max(0.0, min(1.0, availability))

    def _calculate_performance_score(self, employee: Employee) -> float:
        """Calculate performance score based on past tasks rating and consistency (0-1)."""
        from core.models import TaskAssignment
        completed_assignments = TaskAssignment.objects.filter(
            employee=employee, status="COMPLETED"
        )
        if not completed_assignments.exists():
            return 0.5  # Neutral score for new employees without history
            
        total_rating = 0
        count = 0
        ratings = []
        for a in completed_assignments:
            if a.performance_rating:
                total_rating += a.performance_rating
                count += 1
                ratings.append(a.performance_rating)
                
        if count == 0:
            return 0.5
            
        avg_rating = total_rating / count
        
        # Consistency logic
        variance = 0
        if count > 1:
            variance = sum((r - avg_rating) ** 2 for r in ratings) / count
            
        # Penalize high variance
        consistency_penalty = min(0.2, variance * 0.05)
        
        base_score = avg_rating / 5.0
        final_score = base_score - consistency_penalty
        
        return max(0.0, min(1.0, final_score))

    def _match_skill(
        self, required_skill: str, skill_profile: Dict[str, float]
    ) -> float:
        if required_skill in skill_profile:
            return self._confidence_to_score(skill_profile[required_skill], base=0.45)

        required_tokens = set(self._tokenize_skill(required_skill))
        if not required_tokens:
            return 0.0

        best_score = 0.0
        for employee_skill, confidence in skill_profile.items():
            employee_tokens = set(self._tokenize_skill(employee_skill))
            if not employee_tokens:
                continue

            overlap = len(required_tokens & employee_tokens) / len(
                required_tokens | employee_tokens
            )
            if overlap < 0.34:
                continue

            similarity = 0.5 + (0.5 * overlap)
            score = similarity * self._confidence_to_score(confidence, base=0.3)
            if score > best_score:
                best_score = score

        return best_score

    def _best_confidence_for_skill(
        self, required_skill: str, skill_profile: Dict[str, float]
    ) -> float:
        if required_skill in skill_profile:
            return skill_profile[required_skill]

        required_tokens = set(self._tokenize_skill(required_skill))
        if not required_tokens:
            return 0.0

        best_confidence = 0.0
        for employee_skill, confidence in skill_profile.items():
            employee_tokens = set(self._tokenize_skill(employee_skill))
            if not employee_tokens:
                continue

            overlap = len(required_tokens & employee_tokens) / len(
                required_tokens | employee_tokens
            )
            if overlap >= 0.5:
                best_confidence = max(best_confidence, confidence * overlap)

        return best_confidence

    def _tokenize_skill(self, skill: str) -> List[str]:
        tokens = re.split(r"[^a-z0-9]+", (skill or "").lower())
        return [token for token in tokens if len(token) >= 2]

    def _confidence_to_score(self, confidence: float, base: float) -> float:
        bounded = max(0.0, min(1.0, confidence))
        return base + (1.0 - base) * bounded

    def _get_weights(self, priority: Optional[str]) -> Dict[str, float]:
        if not priority:
            return self.weights_by_priority["MEDIUM"]

        return self.weights_by_priority.get(
            priority.upper(), self.weights_by_priority["MEDIUM"]
        )

    def find_best_matches(
        self, task: Task, limit: int = 10, min_score: float = 50.0
    ) -> List[Dict[str, Any]]:
        """
        Find best matching employees for a task.
        Uses efficient DB pre-filtering to minimize python-side processing.

        Args:
            task: Task instance
            limit: Maximum number of matches to return
            min_score: Minimum suitability score to include

        Returns:
            List of dictionaries with employee info and suitability score
        """
        required_skills = task.required_skills
        normalized_required = self._normalize_required_skills(required_skills)
        weights = self._get_weights(task.priority)

        # 1. Base Query with optimization
        # Use annotated workload to filter overloaded employees at DB level
        # Assuming max capacity of MAX_CAPACITY tasks = 100% workload
        from django.conf import settings
        MAX_CAPACITY = settings.EMPLOYEE_MAX_CAPACITY

        employees_query = Employee.objects.select_related("user").prefetch_related(
            "skill_set"
        )

        # Annotate with active task count
        employees_query = employees_query.annotate(
            active_task_count=Count(
                "taskassignment_set",
                filter=Q(
                    taskassignment_set__status__in=[
                        "ASSIGNED",
                        "IN_PROGRESS",
                        "BLOCKED",
                    ]
                ),
            )
        )

        # Filter 1: Exclude fully booked employees (Active tasks < MAX_CAPACITY)
        employees_query = employees_query.filter(active_task_count__lt=MAX_CAPACITY)

        # Filter 2: Pre-filter by skills if any are required
        # This is fuzzy matching limited by SQL capabilities, but significantly reduces candidate pool
        if normalized_required:
            # Create a Q object for OR condition on skill names (case-insensitive)
            # We match if the employee has ANY of the required skills
            skill_filter = Q()
            for skill in normalized_required:
                skill_filter |= Q(skill__name__icontains=skill)

            # Also include employees with relevant titles as a fallback heuristic
            # e.g. if looking for "React", a "Frontend Developer" might be relevant even if skill list is empty
            if "frontend" in " ".join(normalized_required).lower():
                skill_filter |= Q(title__icontains="frontend")
            if "backend" in " ".join(normalized_required).lower():
                skill_filter |= Q(title__icontains="backend")

            # Apply filter (distinct is needed because one employee might match multiple skills)
            employees_query = employees_query.filter(skill_filter).distinct()

        # Execute query
        candidates = list(employees_query)

        if not candidates and normalized_required:
            print(
                "MATCHING_ENGINE: Strict skill filtering yielded 0 candidates. Falling back to workload-only filtering."
            )
            # Fallback: Just filter by workload if skill match was too strict or data is dirty
            employees_query = Employee.objects.select_related("user").prefetch_related(
                "skill_set"
            )
            employees_query = employees_query.annotate(
                active_task_count=Count(
                    "taskassignment_set",
                    filter=Q(
                        taskassignment_set__status__in=[
                            "ASSIGNED",
                            "IN_PROGRESS",
                            "BLOCKED",
                        ]
                    ),
                )
            ).filter(active_task_count__lt=MAX_CAPACITY)
            candidates = list(employees_query)

        matches = []
        for employee in candidates:
            skill_profile = self._build_skill_profile(employee)
            score, breakdown = self._calculate_total_score(
                employee, normalized_required, skill_profile, weights
            )
            
            ml_score = 0.0
            try:
                if hasattr(employee, 'cv') and employee.cv and employee.cv.extracted_text and task.description:
                    ml_score = self.ml_pipeline.calculate_similarity(task.description, employee.cv.extracted_text)
            except Exception as e:
                print(f"ML similarity error for employee {employee.id}: {e}")
                
            breakdown["role_prediction"] = round(ml_score * 100, 1)
                
            if ml_score > 0.0:
                from django.conf import settings
                is_shadow = getattr(settings, 'SHADOW_ML_DEPLOYMENT', True)
                if is_shadow:
                    final_score = score
                else:
                    final_score = (score * 0.7) + (ml_score * 0.3)
            else:
                final_score = score
                
            final_score = round(final_score * 100, 2)
            
            # Use ml_score as confidence, or a fallback heuristic
            confidence_score = round(ml_score * 100, 2) if ml_score > 0 else round(min(1.0, score + 0.1) * 100, 2)

            if final_score >= min_score:
                matches.append(
                    {
                        "employee_id": str(employee.id),
                        "employee_name": employee.name,
                        "employee_title": employee.title or "Employee",
                        "suitability_score": final_score,
                        "ml_confidence_score": confidence_score,
                        "breakdown": breakdown,
                        "matching_skills": self._get_matching_skills(
                            normalized_required, skill_profile
                        ),
                        "missing_skills": self._get_missing_skills(
                            normalized_required, skill_profile
                        ),
                        "current_workload": employee.current_workload,
                        "average_performance": employee.average_performance,
                    }
                )

        matches.sort(key=lambda x: x["suitability_score"], reverse=True)

        return matches[:limit]

    def _get_matching_skills(
        self, required_skills: List[str], skill_profile: Dict[str, float]
    ) -> List[str]:
        """Get list of required skills the employee has (score >= 0.5)."""
        matching = []
        for skill in required_skills:
            if self._match_skill(skill, skill_profile) >= 0.5:
                matching.append(self.skill_extractor.normalize_skill_name(skill))

        return matching

    def _get_missing_skills(
        self, required_skills: List[str], skill_profile: Dict[str, float]
    ) -> List[str]:
        """Get list of required skills the employee is missing (score < 0.5)."""
        missing = []
        for skill in required_skills:
            if self._match_skill(skill, skill_profile) < 0.5:
                missing.append(self.skill_extractor.normalize_skill_name(skill))

        return missing
