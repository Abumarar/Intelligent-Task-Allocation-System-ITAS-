"""
Matching Engine for Task-Employee Suitability Scoring
Calculates how well an employee matches task requirements based on skills, workload, and other factors.
"""
from typing import List, Dict
from django.db.models import Q
from core.models import Employee, Task, Skill, TaskAssignment


class MatchingEngine:
    """Service for calculating task-employee suitability scores."""
    
    def __init__(self):
        self.skill_weight = 0.7  # Weight for skill matching (70%)
        self.workload_weight = 0.2  # Weight for workload balance (20%)
        self.experience_weight = 0.1  # Weight for experience/confidence (10%)
    
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
        if not required_skills:
            # If no skills required, base score on workload only
            workload_score = self._calculate_workload_score(employee)
            return workload_score * 100
        
        # Calculate component scores
        skill_score = self._calculate_skill_match_score(employee, required_skills)
        workload_score = self._calculate_workload_score(employee)
        experience_score = self._calculate_experience_score(employee, required_skills)
        
        # Weighted combination
        total_score = (
            skill_score * self.skill_weight +
            workload_score * self.workload_weight +
            experience_score * self.experience_weight
        )
        
        return round(total_score * 100, 2)
    
    def _calculate_skill_match_score(self, employee: Employee, required_skills: List[str]) -> float:
        """Calculate how well employee skills match required skills (0-1)."""
        if not required_skills:
            return 1.0
        
        employee_skills = set(skill.lower() for skill in employee.skills)
        required_skills_lower = [skill.lower() for skill in required_skills]
        
        # Count matching skills
        matches = sum(1 for skill in required_skills_lower if skill in employee_skills)
        
        # Also check for partial matches (e.g., "react" matches "react.js")
        for req_skill in required_skills_lower:
            if req_skill not in employee_skills:
                # Check for partial matches
                for emp_skill in employee_skills:
                    if req_skill in emp_skill or emp_skill in req_skill:
                        matches += 0.5
                        break
        
        # Score is ratio of matched skills
        match_ratio = min(1.0, matches / len(required_skills))
        
        # Bonus for having extra relevant skills
        if match_ratio > 0.5:
            extra_skills_bonus = min(0.1, (len(employee_skills) - matches) * 0.02)
            match_ratio = min(1.0, match_ratio + extra_skills_bonus)
        
        return match_ratio
    
    def _calculate_workload_score(self, employee: Employee) -> float:
        """Calculate workload score - higher is better (more available) (0-1)."""
        current_workload = employee.current_workload
        
        # Invert workload percentage to get availability score
        # 0% workload = 1.0 score (fully available)
        # 100% workload = 0.0 score (fully booked)
        availability = 1.0 - (current_workload / 100.0)
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, availability))
    
    def _calculate_experience_score(self, employee: Employee, required_skills: List[str]) -> float:
        """Calculate experience score based on skill confidence (0-1)."""
        if not required_skills:
            return 0.5  # Neutral score if no skills required
        
        employee_skills = Skill.objects.filter(employee=employee)
        skill_dict = {skill.name.lower(): skill.confidence_score for skill in employee_skills}
        
        required_skills_lower = [skill.lower() for skill in required_skills]
        matching_skills = [
            skill_dict.get(skill, 0.0) 
            for skill in required_skills_lower 
            if skill in skill_dict
        ]
        
        if not matching_skills:
            return 0.3  # Low score if no matching skills found
        
        # Average confidence score of matching skills
        avg_confidence = sum(matching_skills) / len(matching_skills)
        
        return avg_confidence
    
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
        
        # Get all employees (or filter by some criteria)
        employees = Employee.objects.all()
        
        matches = []
        for employee in employees:
            score = self.calculate_suitability_score(employee, task, required_skills)
            
            if score >= min_score:
                matches.append({
                    'employee_id': str(employee.id),
                    'employee_name': employee.name,
                    'employee_title': employee.title or 'Employee',
                    'suitability_score': score,
                    'matching_skills': self._get_matching_skills(employee, required_skills),
                    'current_workload': employee.current_workload,
                })
        
        # Sort by suitability score (descending)
        matches.sort(key=lambda x: x['suitability_score'], reverse=True)
        
        return matches[:limit]
    
    def _get_matching_skills(self, employee: Employee, required_skills: List[str]) -> List[str]:
        """Get list of skills that match between employee and requirements."""
        employee_skills = set(skill.lower() for skill in employee.skills)
        required_skills_lower = [skill.lower() for skill in required_skills]
        
        matching = [
            skill for skill in required_skills_lower 
            if skill in employee_skills
        ]
        
        return matching
