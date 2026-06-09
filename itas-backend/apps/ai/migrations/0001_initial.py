# Generated manually for apps.ai

from django.db import migrations, models

class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='TrainingData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('employee_id', models.IntegerField(db_index=True)),
                ('task_id', models.IntegerField(db_index=True)),
                ('performance_score', models.FloatField()),
                ('skill_overlap_ratio', models.FloatField(default=0.0)),
                ('missing_required_skills', models.IntegerField(default=0)),
                ('critical_skill_match', models.BooleanField(default=False)),
                ('experience_years', models.FloatField(default=0.0)),
                ('similar_tasks_completed', models.IntegerField(default=0)),
                ('average_rating', models.FloatField(default=0.0)),
                ('success_rate', models.FloatField(default=0.0)),
                ('current_workload_pct', models.FloatField(default=0.0)),
                ('availability_score', models.FloatField(default=0.0)),
                ('semantic_match_score', models.FloatField(default=0.0)),
                ('task_priority_encoded', models.IntegerField(default=1)),
                ('task_complexity_encoded', models.IntegerField(default=1)),
                ('model_version_used', models.CharField(blank=True, max_length=50, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
