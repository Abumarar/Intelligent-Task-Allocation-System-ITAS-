import pytest
from core.models import User, Employee, Task
from core.services.matching_engine import MatchingEngine

@pytest.mark.django_db
def test_matching_engine_empty_task():
    engine = MatchingEngine()
    user = User.objects.create_user(username="test", password="123", role="EMPLOYEE")
    employee = Employee.objects.create(user=user, title="Developer")
    
    pm = User.objects.create_user(username="pm", password="123", role="PM")
    task = Task.objects.create(title="Test Task", priority="MEDIUM", created_by=pm)
    
    score = engine.calculate_suitability_score(employee, task, [])
    assert 0 <= score <= 100
