# Intelligent Task Allocation System (ITAS) - Backend

Backend API for the Intelligent Task Allocation System built with Django REST Framework.

## Features

- **CV Parsing**: Extract text from PDF CVs using PyPDF2
- **Skill Extraction**: Use NLP (spaCy/NLTK) to extract technical skills from CV text
- **Intelligent Matching**: Match tasks to employees based on skills, workload, and suitability scores
- **Task Management**: Create, assign, and track tasks
- **Dashboard Analytics**: Get statistics on tasks, capacity, and skill coverage
- **JWT Authentication**: Secure API access with JSON Web Tokens

## Technology Stack

- **Framework**: Django 4.2.7 + Django REST Framework
- **Database**: PostgreSQL
- **NLP**: spaCy, NLTK
- **PDF Processing**: PyPDF2
- **Authentication**: JWT (PyJWT)

## Setup Instructions

### 1. Prerequisites

- Python 3.8+
- PostgreSQL 12+
- pip/virtualenv

### 2. Install Dependencies

**Option A: Using setup script (Recommended)**
```bash
cd itas-backend
chmod +x setup.sh
./setup.sh
```

**Option B: Manual setup**
```bash
cd itas-backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger'); nltk.download('maxent_ne_chunker'); nltk.download('words')"
```

### 3. Database Setup

Create a PostgreSQL database:

```sql
CREATE DATABASE itas_db;
CREATE USER itas_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE itas_db TO itas_user;
```

### 4. Environment Configuration

Create a `.env` file in the `itas-backend` directory:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=itas_db
DB_USER=itas_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
JWT_SECRET_KEY=your-jwt-secret-key
```

### 5. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser

```bash
python manage.py createsuperuser
```

### 7. Create Initial Users (Optional)

```bash
python manage.py create_demo_users
```

This creates demo users:
- PM user: pm@itas.com / password: pm123
- Employee user: employee@itas.com / password: emp123

### 8. Run Development Server

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/`

## API Endpoints

### Authentication

- `POST /api/auth/login` - Login and get JWT token
  ```json
  {
    "email": "user@example.com",
    "password": "password"
  }
  ```

### Employees

- `GET /api/employees/` - List all employees
- `GET /api/employees/{id}/` - Get employee details
- `POST /api/employees/{id}/cv/` - Upload CV (multipart/form-data)

### Tasks

- `GET /api/tasks/` - List tasks (filtered by user role)
- `POST /api/tasks/` - Create new task
  ```json
  {
    "title": "Task title",
    "description": "Task description",
    "priority": "HIGH|MEDIUM|LOW",
    "requiredSkills": ["React", "Python", "SQL"]
  }
  ```
- `GET /api/tasks/{id}/` - Get task details
- `GET /api/tasks/{id}/matches/` - Get recommended employee matches
- `POST /api/tasks/{id}/assign/` - Assign task to employee
  ```json
  {
    "employee_id": "employee-uuid"
  }
  ```

### Dashboard

- `GET /api/dashboard/stats` - Get dashboard statistics

## Project Structure

```
itas-backend/
├── itas/              # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── core/              # Main application
│   ├── models.py      # Database models
│   ├── views.py       # API views
│   ├── serializers.py # API serializers
│   ├── urls.py        # URL routing
│   ├── admin.py       # Django admin
│   ├── authentication.py  # JWT auth
│   └── services/      # Business logic
│       ├── cv_parser.py
│       ├── skill_extractor.py
│       └── matching_engine.py
├── manage.py
├── requirements.txt
└── README.md
```

## Matching Algorithm

The matching engine calculates suitability scores (0-100) based on:

1. **Skill Matching (70% weight)**: How well employee skills match task requirements
2. **Workload Balance (20% weight)**: Employee's current availability
3. **Experience Level (10% weight)**: Confidence scores from skill extraction

## Development Notes

- CV processing happens asynchronously in background threads
- Skills are extracted using pattern matching and NLP techniques
- The system supports both CV-extracted and manually added skills
- JWT tokens expire after 7 days

## Testing

```bash
python manage.py test
```

## Admin Interface

Access Django admin at `http://localhost:8000/admin/` with superuser credentials.
