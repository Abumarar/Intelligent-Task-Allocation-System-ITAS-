import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "itas.settings.development")
django.setup()

from core.models import Task, Employee
from core.services.matching_engine import MatchingEngine
from django.db import transaction
from core.models import TaskAssignment
from django.utils import timezone

task = Task.objects.first()
employee = Employee.objects.first()

print(f"Assigning task {task.id} to employee {employee.id}")

try:
    engine = MatchingEngine()
    score = engine.calculate_suitability_score(employee, task, task.required_skills)
    
    active_statuses = ["ASSIGNED", "IN_PROGRESS", "BLOCKED"]
    with transaction.atomic():
        TaskAssignment.objects.filter(
            task=task, status__in=active_statuses
        ).exclude(employee=employee).update(status="CANCELLED")
    
        assignment, created = TaskAssignment.objects.get_or_create(
            task=task,
            employee=employee,
            defaults={"suitability_score": score, "status": "ASSIGNED"},
        )
    
        if not created:
            assignment.suitability_score = score
            assignment.status = "ASSIGNED"
            assignment.assigned_at = timezone.now()
            assignment.save()
    
        task.status = "ASSIGNED"
        task.save()
    print("Success!")
except Exception as e:
    import traceback
    traceback.print_exc()
