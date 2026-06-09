import json
import random
import numpy as np
import pandas as pd
from typing import List, Dict

# Settings
NUM_EMPLOYEES = 500
NUM_TASKS = 2000
NUM_ASSIGNMENTS = 50000

np.random.seed(42)
random.seed(42)

ROLES = [
    "Backend Developer", "Frontend Developer", "Full Stack Developer",
    "DevOps Engineer", "Data Engineer", "Data Scientist", "ML Engineer",
    "Mobile Developer", "QA Engineer", "Software Engineer"
]

SENIORITY = ["Junior", "Mid-Level", "Senior", "Lead"]

SKILLS = [
    "Python", "Django", "PostgreSQL", "React", "Vue.js", "Angular", "Node.js",
    "Express", "AWS", "Docker", "Kubernetes", "CI/CD", "Java", "Spring Boot",
    "C#", "ASP.NET", "Go", "Rust", "Data Engineering", "TensorFlow", "PyTorch",
    "REST API", "GraphQL", "MongoDB", "Redis", "TypeScript", "JavaScript",
    "Swift", "Kotlin", "Flutter", "React Native", "Selenium", "Cypress"
]

CERTIFICATIONS = [
    "AWS Cloud Practitioner", "AWS Solutions Architect", "CKA",
    "Google Cloud Professional", "Azure Fundamentals", "Scrum Master", None, None, None
]

def generate_employees() -> pd.DataFrame:
    employees = []
    for i in range(1, NUM_EMPLOYEES + 1):
        role = random.choice(ROLES)
        sen = random.choice(SENIORITY)
        
        # Experience depends on seniority
        if sen == "Junior": exp = round(np.random.uniform(0.5, 3), 1)
        elif sen == "Mid-Level": exp = round(np.random.uniform(3, 6), 1)
        elif sen == "Senior": exp = round(np.random.uniform(6, 12), 1)
        else: exp = round(np.random.uniform(10, 20), 1)
        
        # Skills
        num_skills = random.randint(3, 10)
        emp_skills = random.sample(SKILLS, num_skills)
        
        # Certs
        cert = random.choice(CERTIFICATIONS)
        certs = [cert] if cert else []
        
        # Stats
        gh_score = int(np.random.normal(60, 20))
        gh_score = max(0, min(100, gh_score))
        
        avg_rating = round(np.random.normal(3.8, 0.8), 1)
        avg_rating = max(1.0, min(5.0, avg_rating))
        
        success_rate = round(np.random.normal(0.75, 0.15), 2)
        success_rate = max(0.0, min(1.0, success_rate))
        
        employees.append({
            "employee_id": i,
            "name": f"Employee_{i}",
            "role": role,
            "seniority": sen,
            "years_experience": exp,
            "skills": json.dumps(emp_skills),
            "certifications": json.dumps(certs),
            "github_activity_score": gh_score,
            "average_rating": avg_rating,
            "historical_success_rate": success_rate
        })
    return pd.DataFrame(employees)

def generate_tasks() -> pd.DataFrame:
    tasks = []
    categories = ["Backend", "Frontend", "DevOps", "Mobile", "Machine Learning", "Data Engineering", "QA"]
    priorities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    
    for i in range(1, NUM_TASKS + 1):
        cat = random.choice(categories)
        comp = random.choice([1, 2, 3, 4, 5])
        pri = random.choice(priorities)
        
        # Required skills depend on complexity
        num_skills = random.randint(1, comp + 2)
        req_skills = random.sample(SKILLS, min(num_skills, len(SKILLS)))
        
        est_hours = int(np.random.uniform(comp * 5, comp * 20))
        
        tasks.append({
            "task_id": i,
            "title": f"{cat} Task {i}",
            "description": f"Implementation of {cat} features focusing on {', '.join(req_skills[:2])}.",
            "required_skills": json.dumps(req_skills),
            "complexity": comp,
            "priority": pri,
            "estimated_hours": est_hours
        })
    return pd.DataFrame(tasks)

def generate_assignments(employees_df, tasks_df):
    records = []
    
    emp_dict = employees_df.set_index('employee_id').to_dict('index')
    task_dict = tasks_df.set_index('task_id').to_dict('index')
    
    # Pre-parse json lists
    for k, v in emp_dict.items():
        v['skills_set'] = set(json.loads(v['skills']))
    for k, v in task_dict.items():
        v['req_skills_set'] = set(json.loads(v['required_skills']))
        
    for _ in range(NUM_ASSIGNMENTS):
        task_id = random.randint(1, NUM_TASKS)
        emp_id = random.randint(1, NUM_EMPLOYEES)
        
        emp = emp_dict[emp_id]
        task = task_dict[task_id]
        
        # Feature: skill_overlap
        req = task['req_skills_set']
        have = emp['skills_set']
        
        overlap = len(have.intersection(req))
        skill_overlap = round(overlap / len(req) if req else 1.0, 2)
        missing_required_skills = len(req - have)
        
        critical_skill_match = 1 if missing_required_skills == 0 else 0
        
        years_experience = emp['years_experience']
        
        similar_tasks_completed = random.randint(0, int(years_experience * 5))
        active_tasks = random.randint(0, 8)
        workload_percentage = round(min(1.0, active_tasks / 5.0), 2)
        availability_score = round(max(0.0, 1.0 - workload_percentage), 2)
        
        # Logic for performance and success
        # Base expected performance (1 to 5 scale)
        base_perf = (
            (skill_overlap * 2.0) + 
            (emp['historical_success_rate'] * 1.0) + 
            (emp['average_rating'] * 0.4) +
            (availability_score * 0.5) +
            (min(years_experience / 5.0, 1.0) * 0.5)
        )
        # Add noise
        noise = np.random.normal(0, 0.6)
        perf_score_raw = base_perf + noise
        
        # Scale to 0-100 as requested by the prompt ("performance_score": 91)
        performance_score = int(max(0, min(100, (perf_score_raw / 4.4) * 100)))
        
        # Probability of success
        success_prob = perf_score_raw / 5.0
        # Success is binary
        success = 1 if random.random() < success_prob else 0
        
        records.append({
            "task_id": task_id,
            "employee_id": emp_id,
            "skill_overlap": skill_overlap,
            "critical_skill_match": critical_skill_match,
            "missing_required_skills": missing_required_skills,
            "years_experience": years_experience,
            "similar_tasks_completed": similar_tasks_completed,
            "active_tasks": active_tasks,
            "workload_percentage": workload_percentage,
            "availability_score": availability_score,
            "github_activity_score": emp['github_activity_score'],
            "average_rating": emp['average_rating'],
            "historical_success_rate": emp['historical_success_rate'],
            "success": success,
            "performance_score": performance_score
        })
        
    return pd.DataFrame(records)

print("Generating Employees...")
employees_df = generate_employees()
employees_df.to_csv("itas-backend/ai_training/dataset/employees.csv", index=False)

print("Generating Tasks...")
tasks_df = generate_tasks()
tasks_df.to_csv("itas-backend/ai_training/dataset/tasks.csv", index=False)

print("Generating Assignments...")
assignments_df = generate_assignments(employees_df, tasks_df)
assignments_df.to_csv("itas-backend/ai_training/dataset/task_assignment_training_dataset.csv", index=False)

# Validation Stats
print("\n--- Validation Statistics ---")
print(f"Total Assignments: {len(assignments_df)}")
print(f"Success Rate: {assignments_df['success'].mean():.2f}")
print(f"Avg Performance Score: {assignments_df['performance_score'].mean():.2f}")
print(f"Avg Skill Overlap: {assignments_df['skill_overlap'].mean():.2f}")

corr = assignments_df[['skill_overlap', 'availability_score', 'historical_success_rate', 'performance_score', 'success']].corr()
print("\nCorrelations:")
print(corr)

with open('itas-backend/ai_training/dataset/stats.json', 'w') as f:
    stats = {
        "success_rate": float(assignments_df['success'].mean()),
        "avg_performance": float(assignments_df['performance_score'].mean()),
        "correlations": corr.to_dict()
    }
    json.dump(stats, f)

print("\nDone!")
