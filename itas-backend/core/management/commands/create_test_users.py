from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Employee

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates test users for demo purposes'

    def handle(self, *args, **kwargs):
        # Create PM User
        pm_email = 'pm@itas.com'
        if not User.objects.filter(email=pm_email).exists():
            User.objects.create_user(
                username='pm',
                email=pm_email,
                password='pm123',
                first_name='Sarah',
                last_name='Manager',
                role='PM'
            )
            self.stdout.write(self.style.SUCCESS(f'Created PM user: {pm_email}'))
        else:
            self.stdout.write(self.style.WARNING(f'PM user {pm_email} already exists'))

        # Create Employee User
        emp_email = 'employee@itas.com'
        if not User.objects.filter(email=emp_email).exists():
            user = User.objects.create_user(
                username='employee',
                email=emp_email,
                password='employee123',
                first_name='John',
                last_name='Developer',
                role='EMPLOYEE'
            )
            
            # Create Employee Profile
            if not Employee.objects.filter(user=user).exists():
                Employee.objects.create(
                    user=user,
                    email=emp_email,
                    title='Senior Developer'
                )
            
            self.stdout.write(self.style.SUCCESS(f'Created Employee user: {emp_email}'))
        else:
            self.stdout.write(self.style.WARNING(f'Employee user {emp_email} already exists'))

        # Create Admin User (Superuser)
        admin_email = 'admin@itas.com'
        if not User.objects.filter(email=admin_email).exists():
            User.objects.create_superuser(
                username='admin',
                email=admin_email,
                password='admin123',
                role='PM'  # Admin is also a PM logically
            )
            self.stdout.write(self.style.SUCCESS(f'Created Admin user: {admin_email}'))
        else:
            self.stdout.write(self.style.WARNING(f'Admin user {admin_email} already exists'))
