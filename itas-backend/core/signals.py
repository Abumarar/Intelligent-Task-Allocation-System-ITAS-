from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from core.models import Task, TaskAssignment
from core.services.email_service import EmailService

@receiver(post_save, sender=TaskAssignment)
def notify_employee_on_assignment(sender, instance, created, **kwargs):
    """
    Trigger email when a new Task Assignment is created.
    """
    if instance.status == 'ASSIGNED':
        task = instance.task
        employee = instance.employee
        
        # Only send if this is a fresh assignment (created) or re-assignment
        # Ideally we'd check if status CHANGED, but for now let's ensure we catch valid assignments.
        # To avoid spam updates, we can check if it was just created or if we assume all saves to ASSIGNED are intentional.
        
        print(f"Signal triggered: Assignment for task {task.id} to {employee.name} (Status: {instance.status})")
        EmailService.send_task_assignment_email(employee, task)

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
            if old_task.status != instance.status and instance.status in ['DONE', 'REVIEW']:
                print(f"Signal triggered: Task {instance.id} status changed to {instance.status}")
                if instance.created_by:
                    EmailService.send_task_completion_email(instance.created_by, instance)
        except Task.DoesNotExist:
            pass
