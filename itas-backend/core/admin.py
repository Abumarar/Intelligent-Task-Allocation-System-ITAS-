"""
Django admin configuration
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from core.models import Employee, Task, TaskAssignment, Skill, CV, TaskSkill

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom user admin."""
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_staff']
    list_filter = ['role', 'is_staff', 'is_superuser']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('ITAS Role', {'fields': ('role',)}),
    )


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    """Employee admin."""
    list_display = ['name', 'title', 'email', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'user__email', 'title']


@admin.register(CV)
class CVAdmin(admin.ModelAdmin):
    """CV admin."""
    list_display = ['employee', 'status', 'uploaded_at', 'processed_at']
    list_filter = ['status', 'uploaded_at']
    readonly_fields = ['uploaded_at', 'processed_at', 'extracted_text']


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    """Skill admin."""
    list_display = ['name', 'employee', 'source', 'confidence_score', 'created_at']
    list_filter = ['source', 'created_at']
    search_fields = ['name', 'employee__user__username']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Task admin."""
    list_display = ['title', 'priority', 'status', 'created_by', 'created_at']
    list_filter = ['priority', 'status', 'created_at']
    search_fields = ['title', 'description']


@admin.register(TaskSkill)
class TaskSkillAdmin(admin.ModelAdmin):
    """Task skill admin."""
    list_display = ['task', 'skill_name']
    list_filter = ['skill_name']


@admin.register(TaskAssignment)
class TaskAssignmentAdmin(admin.ModelAdmin):
    """Task assignment admin."""
    list_display = ['task', 'employee', 'suitability_score', 'status', 'assigned_at']
    list_filter = ['status', 'assigned_at']
    search_fields = ['task__title', 'employee__user__username']
