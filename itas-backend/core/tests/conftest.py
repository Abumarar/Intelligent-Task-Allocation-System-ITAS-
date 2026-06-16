import pytest
from rest_framework.test import APIClient
from core.models import User, Employee, Task, Project

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def pm_user():
    user = User.objects.create_user(username="pm_user", password="password123", role="PM")
    return user

@pytest.fixture
def employee_user():
    user = User.objects.create_user(username="emp_user", password="password123", role="EMPLOYEE")
    return user

@pytest.fixture
def employee_profile(employee_user, pm_user):
    return Employee.objects.create(user=employee_user, manager=pm_user, title="Software Engineer")

@pytest.fixture
def sample_project(pm_user):
    return Project.objects.create(title="Test Project", manager=pm_user)

@pytest.fixture
def sample_task(pm_user, sample_project):
    return Task.objects.create(
        title="Test Task", 
        created_by=pm_user, 
        project=sample_project, 
        priority="HIGH"
    )

@pytest.fixture
def pm_client(api_client, pm_user):
    api_client.force_authenticate(user=pm_user)
    return api_client

@pytest.fixture
def employee_client(api_client, employee_user):
    api_client.force_authenticate(user=employee_user)
    return api_client
