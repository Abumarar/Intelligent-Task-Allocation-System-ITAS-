"""
Serializers for API responses
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from core.models import Employee, Task, TaskAssignment, Skill, CV, Project

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """User serializer for API responses."""
    name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'name']
        read_only_fields = ['id', 'role', 'name']
    
    def get_name(self, obj):
        return obj.get_full_name() or obj.username
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Ensure id is a string for frontend compatibility
        data['id'] = str(data['id'])
        return data


class EmployeeSerializer(serializers.ModelSerializer):
    """Employee serializer."""
    name = serializers.CharField(required=False)
    skills = serializers.SerializerMethodField()
    cvStatus = serializers.SerializerMethodField()
    cvUpdatedAt = serializers.SerializerMethodField()
    cvErrorMessage = serializers.SerializerMethodField()
    cvUrl = serializers.SerializerMethodField()
    assigned_tasks = serializers.SerializerMethodField()
    
    class Meta:
        model = Employee
        fields = ['id', 'name', 'title', 'email', 'skills', 'cvStatus', 'cvUpdatedAt', 'cvErrorMessage', 'cvUrl', 'current_workload', 'assigned_tasks']
        read_only_fields = ['id']
    
    def get_assigned_tasks(self, obj):
        assignments = obj.taskassignment_set.filter(
            status__in=['ASSIGNED', 'IN_PROGRESS', 'BLOCKED']
        ).select_related('task')
        
        return [{
            'id': str(a.task.id),
            'title': a.task.title,
            'status': a.status,
            'priority': a.task.priority,
            'due_date': a.task.due_date,
            'suitability_score': a.suitability_score
        } for a in assignments]

    def get_skills(self, obj):
        return obj.skills
    
    def get_cvStatus(self, obj):
        if hasattr(obj, 'cv'):
            return obj.cv.status
        return 'NOT_UPLOADED'
    
    def get_cvUpdatedAt(self, obj):
        if hasattr(obj, 'cv') and obj.cv.uploaded_at:
            return obj.cv.uploaded_at.isoformat()
        return None

    def get_cvErrorMessage(self, obj):
        if hasattr(obj, 'cv') and obj.cv.status == 'FAILED':
            return obj.cv.error_message
        return None

    def get_cvUrl(self, obj):
        if hasattr(obj, 'cv') and obj.cv.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cv.file.url)
            return obj.cv.file.url
        return None

    def update(self, instance, validated_data):
        """Update employee and associated user."""
        # Update direct fields
        instance.title = validated_data.get('title', instance.title)
        instance.email = validated_data.get('email', instance.email)
        instance.save()

        # Update User fields if name or email provided
        user = instance.user
        name = validated_data.get('name')
        
        if name:
            parts = name.strip().split()
            if parts:
                user.first_name = parts[0]
                user.last_name = ' '.join(parts[1:]) if len(parts) > 1 else ''
        
        if validated_data.get('email'):
            user.email = validated_data.get('email')
            
        user.save()
        return instance


class ProjectSerializer(serializers.ModelSerializer):
    """Serializer for projects."""
    manager_name = serializers.CharField(source='manager.get_full_name', read_only=True)
    task_count = serializers.SerializerMethodField()
    completed_task_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id', 'title', 'description', 'manager', 'manager_name', 'status', 'created_at', 'updated_at', 'task_count', 'completed_task_count']
        read_only_fields = ['id', 'manager', 'created_at', 'updated_at']

    def get_task_count(self, obj):
        return obj.tasks.count()

    def get_completed_task_count(self, obj):
        return obj.tasks.filter(status='COMPLETED').count()


class TaskSkillSerializer(serializers.Serializer):
    """Serializer for task skills."""
    skill_name = serializers.CharField(max_length=100)





class TaskSerializer(serializers.ModelSerializer):
    """Task serializer."""
    requiredSkills = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    assigned_to = serializers.SerializerMethodField()
    assigned_to_name = serializers.SerializerMethodField()
    project_id = serializers.PrimaryKeyRelatedField(source='project', queryset=Project.objects.all(), allow_null=True, required=False)
    project_title = serializers.CharField(source='project.title', read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'priority', 'status', 
            'requiredSkills', 'created_by', 'created_by_name',
            'created_at', 'updated_at', 'start_date', 'due_date',
            'assigned_to', 'assigned_to_name', 'project_id', 'project_title'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']
    
    def get_requiredSkills(self, obj):
        return obj.required_skills
    
    def get_assigned_to(self, obj):
        """Get ID of currently assigned employee."""
        assignment = obj.assignments.filter(
            status__in=['ASSIGNED', 'IN_PROGRESS', 'BLOCKED']
        ).order_by('-assigned_at').first()
        return str(assignment.employee.id) if assignment else None

    def get_assigned_to_name(self, obj):
        """Get name of currently assigned employee."""
        assignment = obj.assignments.filter(
            status__in=['ASSIGNED', 'IN_PROGRESS', 'BLOCKED']
        ).order_by('-assigned_at').first()
        return assignment.employee.name if assignment else None
    
    def create(self, validated_data):
        # Get required skills from request data
        required_skills = self.context['request'].data.get('requiredSkills', [])
        
        # Create task
        task = Task.objects.create(**validated_data)
        
        # Create task skills
        for skill_name in required_skills:
            if skill_name:
                task.task_skills.create(skill_name=skill_name)
        
        return task


class TaskMatchSerializer(serializers.Serializer):
    """Serializer for task-employee matches."""
    employee_id = serializers.CharField()
    employee_name = serializers.CharField()
    employee_title = serializers.CharField()
    suitability_score = serializers.FloatField()
    matching_skills = serializers.ListField(child=serializers.CharField())
    current_workload = serializers.FloatField()


class TaskAssignmentSerializer(serializers.ModelSerializer):
    """Task assignment serializer."""
    employee_name = serializers.CharField(source='employee.name', read_only=True)
    task_title = serializers.CharField(source='task.title', read_only=True)
    
    class Meta:
        model = TaskAssignment
        fields = [
            'id', 'task', 'task_title', 'employee', 'employee_name',
            'suitability_score', 'status', 'assigned_at', 
            'started_at', 'completed_at'
        ]
        read_only_fields = ['id', 'assigned_at']


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics."""
    active_tasks = serializers.IntegerField()
    unassigned_tasks = serializers.IntegerField()
    employee_capacity = serializers.FloatField()
    skills_coverage = serializers.FloatField()
