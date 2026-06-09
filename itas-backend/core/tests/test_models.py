from django.test import TestCase
from django.contrib.auth import get_user_model
from django.conf import settings
from core.models import Employee, Task, TaskAssignment, TaskSkill

User = get_user_model()

class EmployeeModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@test.com', password='pw')
        self.employee = Employee.objects.create(user=self.user, name="Test Emp")
        self.manager = User.objects.create_user(username='pm', email='pm@test.com', password='pw')
        self.project = None # Can create if needed, task allows null project usually

    def test_employee_workload_calculation(self):
        # Create 3 active tasks
        for i in range(3):
            t = Task.objects.create(title=f"T{i}", created_by=self.manager)
            TaskAssignment.objects.create(task=t, employee=self.employee, status="ASSIGNED")
            
        workload = self.employee.current_workload
        # Max capacity is from settings, but let's assume it's 5 as per standard config
        expected = (3 / settings.EMPLOYEE_MAX_CAPACITY) * 100 if settings.EMPLOYEE_MAX_CAPACITY > 0 else 0
        self.assertAlmostEqual(workload, expected)

    def test_employee_workload_max_cap(self):
        # Create 6 active tasks
        for i in range(6):
            t = Task.objects.create(title=f"T{i}", created_by=self.manager)
            TaskAssignment.objects.create(task=t, employee=self.employee, status="ASSIGNED")
            
        workload = self.employee.current_workload
        self.assertEqual(workload, 100)

    def test_average_performance_no_history(self):
        self.assertIsNone(self.employee.average_performance)


class TaskModelTest(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(username='pm', email='pm@test.com', password='pw')
        self.task = Task.objects.create(title="Test Task", created_by=self.manager)

    def test_task_required_skills_property(self):
        TaskSkill.objects.create(task=self.task, name="Python")
        TaskSkill.objects.create(task=self.task, name="Django")
        
        skills = self.task.required_skills
        self.assertIn("Python", skills)
        self.assertIn("Django", skills)
        self.assertEqual(len(skills), 2)
