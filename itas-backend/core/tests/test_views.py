import pytest
from django.urls import reverse
from core.models import Task, Employee, User, TaskAssignment

@pytest.mark.django_db
class TestEmployeeViews:
    def test_analyze_cv_no_file(self, pm_client):
        url = reverse("employee-analyze-cv")
        response = pm_client.post(url, {})
        assert response.status_code == 400
        
    def test_get_my_profile(self, employee_client, employee_profile):
        url = reverse("employee-get-my-profile")
        response = employee_client.get(url)
        assert response.status_code == 200
        assert response.data["employee"]["name"] == employee_profile.name

@pytest.mark.django_db
class TestTaskViews:
    def test_analyze_document_no_file(self, pm_client):
        url = reverse("task-analyze-document")
        response = pm_client.post(url, {})
        assert response.status_code == 400

    def test_assign_task(self, pm_client, sample_task, employee_profile):
        url = reverse("task-assign-task", args=[sample_task.id])
        response = pm_client.post(url, {"employee_id": employee_profile.id})
        assert response.status_code == 200

    def test_unassign_task(self, pm_client, sample_task):
        url = reverse("task-unassign-task", args=[sample_task.id])
        response = pm_client.post(url, {})
        assert response.status_code == 200

    def test_update_progress(self, employee_client, sample_task, employee_profile):
        TaskAssignment.objects.create(task=sample_task, employee=employee_profile, status="ASSIGNED", suitability_score=90.0)
        url = reverse("task-update-progress", args=[sample_task.id])
        response = employee_client.post(url, {"status": "IN_PROGRESS", "notes": "Started working"})
        assert response.status_code == 200
        
    def test_rate_performance(self, pm_client, sample_task, employee_profile):
        TaskAssignment.objects.create(task=sample_task, employee=employee_profile, status="COMPLETED", suitability_score=90.0)
        url = reverse("task-rate-performance", args=[sample_task.id])
        response = pm_client.post(url, {
            "quality_rating": 4, 
            "timeliness_rating": 5, 
            "communication_rating": 4, 
            "technical_rating": 4
        })
        assert response.status_code == 200
