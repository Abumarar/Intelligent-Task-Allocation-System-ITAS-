from django.db import models

class TrainingData(models.Model):
    """Stores tabular features for offline ML training and evaluation."""
    
    employee_id = models.IntegerField(db_index=True)
    task_id = models.IntegerField(db_index=True)
    
    # Target Variable
    performance_score = models.FloatField(help_text="Target variable from 0 to 5.0")
    
    # Skill Features
    skill_overlap_ratio = models.FloatField(default=0.0)
    missing_required_skills = models.IntegerField(default=0)
    critical_skill_match = models.BooleanField(default=False)
    
    # Experience Features
    experience_years = models.FloatField(default=0.0)
    similar_tasks_completed = models.IntegerField(default=0)
    
    # Performance Features
    average_rating = models.FloatField(default=0.0)
    success_rate = models.FloatField(default=0.0)
    
    # Workload Features
    current_workload_pct = models.FloatField(default=0.0)
    availability_score = models.FloatField(default=0.0)
    
    # Semantic Match Feature
    semantic_match_score = models.FloatField(default=0.0)
    
    # Task Context
    task_priority_encoded = models.IntegerField(default=1)
    task_complexity_encoded = models.IntegerField(default=1)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    model_version_used = models.CharField(max_length=50, blank=True, null=True, help_text="Version of the ranker that made the assignment")

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Training Data"

    def __str__(self):
        return f"Training Data for Emp {self.employee_id} - Task {self.task_id}"
