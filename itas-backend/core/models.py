from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    """Custom user model with role-based access."""
    ROLE_CHOICES = [
        ('PM', 'Project Manager'),
        ('EMPLOYEE', 'Employee'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='EMPLOYEE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} ({self.role})"


class Employee(models.Model):
    """Employee profile with CV and skill information."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_employees')
    title = models.CharField(max_length=200, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.title or 'Employee'}"

    @property
    def name(self):
        return self.user.get_full_name() or self.user.username

    @property
    def skills(self):
        """Get all skills associated with this employee."""
        return list(self.skill_set.values_list('name', flat=True))

    @property
    def current_workload(self):
        """Calculate current workload as percentage of capacity."""
        active_tasks = self.taskassignment_set.filter(
            status__in=['ASSIGNED', 'IN_PROGRESS', 'BLOCKED']
        ).count()
        # Assuming max capacity of 5 active tasks = 100%
        max_capacity = 5
        return min(100, (active_tasks / max_capacity) * 100) if max_capacity > 0 else 0


class CV(models.Model):
    """CV/Portfolio document uploaded by employee."""
    STATUS_CHOICES = [
        ('NOT_UPLOADED', 'Not Uploaded'),
        ('PROCESSING', 'Processing'),
        ('READY', 'Ready'),
        ('FAILED', 'Failed'),
    ]

    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='cv')
    file = models.FileField(upload_to='cvs/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NOT_UPLOADED')
    extracted_text = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"CV for {self.employee.name} - {self.status}"



class Skill(models.Model):
    """Skills extracted from CVs or manually added."""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    source = models.CharField(
        max_length=20,
        choices=[('CV', 'CV'), ('MANUAL', 'Manual'), ('PORTFOLIO', 'Portfolio')],
        default='CV'
    )
    confidence_score = models.FloatField(default=0.0, help_text="Confidence score from NLP extraction")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['employee', 'name']
        ordering = ['-confidence_score', 'name']

    def __str__(self):
        return f"{self.employee.name} - {self.name}"


class Project(models.Model):
    """A collection of tasks managed by a PM."""
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    manager = models.ForeignKey(User, on_delete=models.CASCADE, related_name='managed_projects')
    status = models.CharField(max_length=20, default='ACTIVE', choices=[
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('ARCHIVED', 'Archived')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title


class Task(models.Model):
    """Task definition with requirements and skill needs."""
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
    ]

    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('UNASSIGNED', 'Unassigned'),
        ('ASSIGNED', 'Assigned'),
        ('IN_PROGRESS', 'In Progress'),
        ('BLOCKED', 'Blocked'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    title = models.CharField(max_length=300)
    description = models.TextField(blank=True, null=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    start_date = models.DateTimeField(blank=True, null=True)
    due_date = models.DateTimeField(blank=True, null=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.priority})"

    @property
    def required_skills(self):
        """Get all required skills for this task."""
        return list(self.task_skills.values_list('skill_name', flat=True))


class TaskSkill(models.Model):
    """Required skills for a task."""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='task_skills')
    skill_name = models.CharField(max_length=100)

    class Meta:
        unique_together = ['task', 'skill_name']

    def __str__(self):
        return f"{self.task.title} requires {self.skill_name}"


class TaskAssignment(models.Model):
    """Assignment of task to employee with suitability score."""
    STATUS_CHOICES = [
        ('ASSIGNED', 'Assigned'),
        ('IN_PROGRESS', 'In Progress'),
        ('BLOCKED', 'Blocked'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='assignments')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='taskassignment_set')
    suitability_score = models.FloatField(
        help_text="Score from 0-100 indicating how well employee matches task requirements"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ASSIGNED')
    assigned_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ['task', 'employee']
        ordering = ['-suitability_score']

    def __str__(self):
        return f"{self.task.title} -> {self.employee.name} ({self.suitability_score:.1f}%)"
