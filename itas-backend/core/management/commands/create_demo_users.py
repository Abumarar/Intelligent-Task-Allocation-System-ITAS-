"""
Management command to create demo users for testing
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Employee, Skill

User = get_user_model()


class Command(BaseCommand):
    help = 'Create demo users (PM and Employee) for testing'

    def handle(self, *args, **options):
        # Create PM user
        pm_user, created = User.objects.get_or_create(
            username='pm@itas.com',
            defaults={
                'email': 'pm@itas.com',
                'first_name': 'Demo',
                'last_name': 'PM',
                'role': 'PM',
                'is_staff': True,
            }
        )
        if created:
            pm_user.set_password('pm123')
            pm_user.save()
            self.stdout.write(self.style.SUCCESS(f'Created PM user: {pm_user.username}'))
        else:
            # Update password in case it was changed
            pm_user.set_password('pm123')
            pm_user.save()
            self.stdout.write(self.style.WARNING(f'PM user already exists: {pm_user.username}'))

        # Create Employee user
        emp_user, created = User.objects.get_or_create(
            username='employee@itas.com',
            defaults={
                'email': 'employee@itas.com',
                'first_name': 'Demo',
                'last_name': 'Employee',
                'role': 'EMPLOYEE',
            }
        )
        if created:
            emp_user.set_password('emp123')
            emp_user.save()
            self.stdout.write(self.style.SUCCESS(f'Created Employee user: {emp_user.username}'))
        else:
            # Update password in case it was changed
            emp_user.set_password('emp123')
            emp_user.save()
            self.stdout.write(self.style.WARNING(f'Employee user already exists: {emp_user.username}'))
            
        # Create employee profile
        employee, emp_created = Employee.objects.get_or_create(
            user=emp_user,
            defaults={
                'title': 'Software Developer',
                'email': 'employee@itas.com',
            }
        )
        
        if emp_created:
            # Add some sample skills
            sample_skills = [
                {'name': 'Python', 'confidence': 0.9},
                {'name': 'React', 'confidence': 0.8},
                {'name': 'SQL', 'confidence': 0.7},
                {'name': 'JavaScript', 'confidence': 0.85},
                {'name': 'Django', 'confidence': 0.75},
            ]
            
            for skill_data in sample_skills:
                Skill.objects.create(
                    employee=employee,
                    name=skill_data['name'],
                    source='MANUAL',
                    confidence_score=skill_data['confidence']
                )
            
            self.stdout.write(self.style.SUCCESS(f'Created employee profile with skills'))

        self.stdout.write(self.style.SUCCESS('\nDemo users created successfully!'))
        self.stdout.write(self.style.SUCCESS('PM: pm@itas.com / pm123'))
        self.stdout.write(self.style.SUCCESS('Employee: employee@itas.com / emp123'))
