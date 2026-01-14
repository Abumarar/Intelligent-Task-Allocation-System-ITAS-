"""
Matching Engine for Task-Employee Suitability Scoring
Calculates how well an employee matches task requirements based on skills, workload, and other factors.
"""
from typing import List, Dict
import re
from core.models import Employee, Task
from core.services.skill_extractor import SkillExtractor


class MatchingEngine:
    """Service for calculating task-employee suitability scores."""

    def __init__(self):
        self.weights_by_priority = {
            "HIGH": {"skill": 0.6, "coverage": 0.15, "experience": 0.15, "workload": 0.1},
            "MEDIUM": {"skill": 0.55, "coverage": 0.15, "experience": 0.1, "workload": 0.2},
            "LOW": {"skill": 0.45, "coverage": 0.15, "experience": 0.1, "workload": 0.3},
        }
        self.skill_extractor = SkillExtractor()

    def calculate_suitability_score(
        self,
        employee: Employee,
        task: Task,
        required_skills: List[str]
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

        total_score = self._calculate_total_score(
            employee,
            normalized_required,
            skill_profile,
            weights
        )

        return round(total_score * 100, 2)

    def _calculate_total_score(
        self,
        employee: Employee,
        normalized_required: List[str],
        skill_profile: Dict[str, float],
        weights: Dict[str, float]
    ) -> float:
        if not normalized_required:
            workload_score = self._calculate_workload_score(employee)
            return workload_score

        skill_score = self._calculate_skill_match_score(skill_profile, normalized_required)
        coverage_score = self._calculate_coverage_score(skill_profile, normalized_required)
        experience_score = self._calculate_experience_score(skill_profile, normalized_required)
        workload_score = self._calculate_workload_score(employee)

        total_score = (
            skill_score * weights["skill"] +
            coverage_score * weights["coverage"] +
            experience_score * weights["experience"] +
            workload_score * weights["workload"]
        )

        return max(0.0, min(1.0, total_score))

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

        return skill_profile

    def _calculate_skill_match_score(
        self,
        skill_profile: Dict[str, float],
        required_skills: List[str]
    ) -> float:
        if not required_skills:
            return 1.0

        scores = [self._match_skill(skill, skill_profile) for skill in required_skills]
        return sum(scores) / len(required_skills)

    def _calculate_coverage_score(
        self,
        skill_profile: Dict[str, float],
        required_skills: List[str]
    ) -> float:
        if not required_skills:
            return 1.0

        matched = sum(
            1 for skill in required_skills
            if self._match_skill(skill, skill_profile) >= 0.5
        )
        return matched / len(required_skills)

    def _calculate_experience_score(
        self,
        skill_profile: Dict[str, float],
        required_skills: List[str]
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

    def _match_skill(self, required_skill: str, skill_profile: Dict[str, float]) -> float:
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

            overlap = len(required_tokens & employee_tokens) / len(required_tokens | employee_tokens)
            if overlap < 0.34:
                continue

            similarity = 0.5 + (0.5 * overlap)
            score = similarity * self._confidence_to_score(confidence, base=0.3)
            if score > best_score:
                best_score = score

        return best_score

    def _best_confidence_for_skill(self, required_skill: str, skill_profile: Dict[str, float]) -> float:
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

            overlap = len(required_tokens & employee_tokens) / len(required_tokens | employee_tokens)
            if overlap >= 0.5:
                best_confidence = max(best_confidence, confidence * overlap)

        return best_confidence

    def _tokenize_skill(self, skill: str) -> List[str]:
        tokens = re.split(r"[^a-z0-9]+", (skill or "").lower())
        return [token for token in tokens if len(token) >= 2]

    def _confidence_to_score(self, confidence: float, base: float) -> float:
        bounded = max(0.0, min(1.0, confidence))
        return base + (1.0 - base) * bounded

    def _get_weights(self, priority: str) -> Dict[str, float]:
        if not priority:
            return self.weights_by_priority["MEDIUM"]

        return self.weights_by_priority.get(priority.upper(), self.weights_by_priority["MEDIUM"])

    def find_best_matches(
        self,
        task: Task,
        limit: int = 10,
        min_score: float = 50.0
    ) -> List[Dict]:
        """
        Find best matching employees for a task.

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

        employees = Employee.objects.select_related("user").prefetch_related("skill_set")

        matches = []
        for employee in employees:
            skill_profile = self._build_skill_profile(employee)
            score = self._calculate_total_score(
                employee,
                normalized_required,
                skill_profile,
                weights
            )
            score = round(score * 100, 2)

            if score >= min_score:
                matches.append({
                    "employee_id": str(employee.id),
                    "employee_name": employee.name,
                    "employee_title": employee.title or "Employee",
                    "suitability_score": score,
                    "matching_skills": self._get_matching_skills(
                        normalized_required,
                        skill_profile
                    ),
                    "current_workload": employee.current_workload,
                })

        matches.sort(key=lambda x: x["suitability_score"], reverse=True)

        return matches[:limit]

    def _get_matching_skills(
        self,
        required_skills: List[str],
        skill_profile: Dict[str, float]
    ) -> List[str]:
        """Get list of skills that match between employee and requirements."""
        matching = []
        for skill in required_skills:
            if self._match_skill(skill, skill_profile) >= 0.5:
                matching.append(self.skill_extractor.normalize_skill_name(skill))

        return matching
