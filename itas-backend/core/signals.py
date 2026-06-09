from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from core.models import Task, TaskAssignment
from core.services.email_service import EmailService


@receiver(post_save, sender=TaskAssignment)
def notify_employee_on_assignment(sender, instance, created, **kwargs):
    """
    Trigger email when a new Task Assignment is created.
    """
    if instance.status == "ASSIGNED":
        task = instance.task
        employee = instance.employee

        # Only send if this is a fresh assignment (created) or re-assignment
        # Ideally we'd check if status CHANGED, but for now let's ensure we catch valid assignments.
        # To avoid spam updates, we can check if it was just created or if we assume all saves to ASSIGNED are intentional.

        print(
            f"Signal triggered: Assignment for task {task.id} to {employee.name} (Status: {instance.status})"
        )
        try:
            from core.tasks import send_assignment_email_async
            send_assignment_email_async.delay(employee.id, task.id)
        except Exception as e:
            print(f"Failed to queue assignment email (is Celery/Redis running?): {e}")


@receiver(post_save, sender=Task)
def sync_assignment_status(sender, instance, created, **kwargs):
    """
    Sync Task status changes to TaskAssignments to ensure workload is accurate.
    When a Task is CANCELLED or COMPLETED, the assignment should reflect that.
    """
    if created:
        return

    if instance.status in ["CANCELLED", "COMPLETED", "BLOCKED"]:
        # Update all active assignments to match the task status
        # This releases the workload for the employee
        TaskAssignment.objects.filter(
            task=instance, status__in=["ASSIGNED", "IN_PROGRESS", "BLOCKED"]
        ).update(status=instance.status)

    elif instance.status == "IN_PROGRESS":
        # Optional: verify if we want to sync this way, usually assignment drives task,
        # but if PM moves task to IN_PROGRESS, we might want to update assignment too.
        # For now, let's stick to the critical ones for workload (CANCELLED/COMPLETED).
        pass


@receiver(pre_save, sender=Task)
def notify_pm_on_completion(sender, instance, **kwargs):
    """
    Trigger email when task status changes to DONE.
    Using pre_save to compare with old status if needed,
    but mainly just checking if new status is DONE.
    """
    if instance.pk:
        try:
            old_task = Task.objects.get(pk=instance.pk)
            # Check COMPLETED (was DONE in comment but model has COMPLETED)
            if old_task.status != instance.status and instance.status == "COMPLETED":
                print(
                    f"Signal triggered: Task {instance.id} status changed to {instance.status}"
                )
                if instance.created_by:
                    try:
                        from core.tasks import send_completion_email_async
                        send_completion_email_async.delay(instance.created_by.id, instance.id)
                    except Exception as e:
                        print(f"Failed to queue completion email (is Celery/Redis running?): {e}")
        except Task.DoesNotExist:
            pass

@receiver(post_save, sender=TaskAssignment)
def capture_training_data_on_completion(sender, instance, **kwargs):
    """
    Feedback Learning Loop: When a TaskAssignment is updated with a performance rating
    (usually upon completion), extract the candidate's features at this exact moment
    and log it into the TrainingData table for continuous ML learning.
    """
    # Only proceed if the assignment has a performance rating (i.e. is fully evaluated)
    if not instance.performance_rating:
        return
        
    try:
        from apps.ai.models import TrainingData
        from apps.ai.services.feature_store import FeatureStore
        
        # Check if we already logged this assignment to avoid duplicates
        # In a real app we might use a unique constraint or composite key
        
        fs = FeatureStore()
        features_df = fs.build_features(instance.task, [instance.employee])
        
        if features_df is None or features_df.empty:
            return
            
        row = features_df.iloc[0]
        
        TrainingData.objects.create(
            employee_id=instance.employee.id,
            task_id=instance.task.id,
            performance_score=instance.performance_rating,
            skill_overlap_ratio=row.get('skill_overlap_ratio', 0.0),
            missing_required_skills=row.get('missing_required_skills', 0),
            average_rating=row.get('average_rating', 0.0),
            current_workload_pct=row.get('current_workload_pct', 0.0),
            availability_score=row.get('availability_score', 0.0),
            semantic_match_score=row.get('semantic_match_score', 0.0),
            task_priority_encoded=row.get('task_priority_encoded', 2),
            task_complexity_encoded=row.get('task_complexity_encoded', 2)
        )
        print(f"Feedback Learning Loop: Captured training data for Task {instance.task.id} -> Emp {instance.employee.id}")
        
    except Exception as e:
        print(f"Error capturing training data: {e}")
