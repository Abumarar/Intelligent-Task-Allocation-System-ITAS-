from django.core.mail import send_mail
from django.conf import settings
from core.models import Task, Employee, User

class EmailService:
    @staticmethod
    def send_task_assignment_email(employee: Employee, task: Task):
        """
        Notify employee about a new task assignment.
        """
        if not employee.email:
            return

        subject = f"New Task Assigned: {task.title}"
        message = f"""
        Hello {employee.name},

        You have been assigned a new task:
        
        Title: {task.title}
        Priority: {task.priority}
        Due Date: {task.due_date if task.due_date else 'Not specified'}

        Description:
        {task.description}

        Please log in to the system to view more details.
        
        Best regards,
        ITAS Team
        """
        
        EmailService.send_email(subject, message, [employee.email])

    @staticmethod
    def send_task_completion_email(pm: User, task: Task):
        """
        Notify PM when a task created by them is completed.
        """
        if not pm.email:
            return

        subject = f"Task Completed: {task.title}"
        message = f"""
        Hello {pm.get_full_name() or pm.username},

        The task "{task.title}" has been marked as {task.status}.

        Assignee: {task.assignments.first().employee.name if task.assignments.exists() else 'Unknown'}
        
        Please log in to review.

        Best regards,
        ITAS Team
        """
        
        EmailService.send_email(subject, message, [pm.email])

    @staticmethod
    def send_email(subject, message, recipient_list):
        def _send():
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    recipient_list,
                    fail_silently=True,  # Don't crash app if email fails
                )
                print(f"Email sent to {recipient_list}: {subject}")
            except Exception as e:
                print(f"Failed to send email: {e}")
        
        # Run in a separate thread to avoid blocking
        import threading
        email_thread = threading.Thread(target=_send)
        email_thread.daemon = True
        email_thread.start()
