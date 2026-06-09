from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from core.models import Employee, Task, TaskAssignment, TaskSkill, Skill, Project
from core.services.matching_engine import MatchingEngine

User = get_user_model()

class MatchingEngineTest(TestCase):
    def setUp(self):
        self.pm = User.objects.create_user(username='pm', email='pm@test.com', password='pw')
        self.user = User.objects.create_user(username='emp', email='emp@test.com', password='pw')
        self.employee = Employee.objects.create(user=self.user, name="Test Emp")
        self.engine = MatchingEngine()
        
        self.task = Task.objects.create(title="Test Task", priority="MEDIUM", created_by=self.pm)

    def test_perfect_skill_match(self):
        TaskSkill.objects.create(task=self.task, name="Python")
        TaskSkill.objects.create(task=self.task, name="Django")
        Skill.objects.create(employee=self.employee, name="Python", confidence_score=1.0)
        Skill.objects.create(employee=self.employee, name="Django", confidence_score=1.0)
        
        score = self.engine.calculate_suitability_score(self.employee, self.task, self.task.required_skills)
        self.assertGreater(score, 80.0)

    def test_no_skills(self):
        TaskSkill.objects.create(task=self.task, name="Python")
        # Employee has no skills
        score = self.engine.calculate_suitability_score(self.employee, self.task, self.task.required_skills)
        self.assertLess(score, 50.0)

    def test_overloaded_employee(self):
        # Create perfect skills
        TaskSkill.objects.create(task=self.task, name="Python")
        Skill.objects.create(employee=self.employee, name="Python", confidence_score=1.0)
        
        # Load employee to 100% capacity (assuming >= 5 tasks)
        for i in range(6):
            t = Task.objects.create(title=f"T{i}", created_by=self.pm)
            TaskAssignment.objects.create(task=t, employee=self.employee, status="ASSIGNED")
            
        score = self.engine.calculate_suitability_score(self.employee, self.task, self.task.required_skills)
        # Without load, score > 80. With load, it should be heavily penalized
        self.assertLess(score, 70.0)

    def test_empty_required_skills(self):
        # Task has no required skills
        score = self.engine.calculate_suitability_score(self.employee, self.task, [])
        self.assertIsNotNone(score)
        self.assertGreater(score, 0)

    def test_priority_weights(self):
        # HIGH priority gives more weight to skills
        TaskSkill.objects.create(task=self.task, name="Python")
        Skill.objects.create(employee=self.employee, name="Python", confidence_score=1.0)
        
        self.task.priority = "LOW"
        low_priority_score = self.engine.calculate_suitability_score(self.employee, self.task, self.task.required_skills)
        
        self.task.priority = "HIGH"
        high_priority_score = self.engine.calculate_suitability_score(self.employee, self.task, self.task.required_skills)
        
        # High priority should focus heavily on the perfect skill match
        self.assertNotEqual(low_priority_score, high_priority_score)

    def test_new_employee_neutral_performance(self):
        perf_score = self.engine._calculate_performance_score(self.employee, self.task)
        self.assertEqual(perf_score, 0.5)
