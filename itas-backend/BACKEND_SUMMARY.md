# ITAS Backend - Implementation Summary

## Overview
Complete Django REST Framework backend for the Intelligent Task Allocation System (ITAS) as specified in the project documentation.

## Core Components

### 1. Database Models (`core/models.py`)
- **User**: Custom user model with role-based access (PM/EMPLOYEE)
- **Employee**: Employee profiles with title, email, and skills
- **CV**: CV/Portfolio document storage with processing status
- **Skill**: Skills extracted from CVs or manually added
- **Task**: Task definitions with priority, status, and requirements
- **TaskSkill**: Required skills for tasks
- **TaskAssignment**: Task-employee assignments with suitability scores

### 2. Services (`core/services/`)

#### CV Parser (`cv_parser.py`)
- Extracts text from PDF CV files using PyPDF2
- Validates PDF files
- Handles file reading and error cases

#### Skill Extractor (`skill_extractor.py`)
- Uses NLTK for NLP processing
- Pattern matching against technical skills database
- Extracts skills from dedicated CV sections
- Identifies compound skills (multi-word phrases)
- Normalizes skill names
- Provides confidence scores for extracted skills

#### Matching Engine (`matching_engine.py`)
- Calculates suitability scores (0-100) for task-employee matches
- Considers:
  - Skill matching (70% weight)
  - Workload balance (20% weight)
  - Experience level (10% weight)
- Finds best matches for tasks
- Supports partial skill matching

### 3. API Endpoints (`core/views.py`, `core/urls.py`)

#### Authentication
- `POST /api/auth/login` - User login with JWT token generation

#### Employees
- `GET /api/employees/` - List all employees
- `GET /api/employees/{id}/` - Get employee details
- `POST /api/employees/{id}/cv/` - Upload and process CV (async)

#### Tasks
- `GET /api/tasks/` - List tasks (role-filtered)
- `POST /api/tasks/` - Create new task
- `GET /api/tasks/{id}/` - Get task details
- `GET /api/tasks/{id}/matches/` - Get recommended employee matches
- `POST /api/tasks/{id}/assign/` - Assign task to employee

#### Dashboard
- `GET /api/dashboard/stats` - Get dashboard statistics

### 4. Authentication (`core/authentication.py`)
- JWT-based authentication
- Token generation with 7-day expiration
- Supports demo mode for development
- Custom authentication class for DRF

### 5. Serializers (`core/serializers.py`)
- User, Employee, Task serializers
- Task match and assignment serializers
- Dashboard statistics serializer
- Proper data transformation for frontend compatibility

### 6. Admin Interface (`core/admin.py`)
- Django admin configuration for all models
- User-friendly list displays and filters
- Search functionality

## Key Features Implemented

✅ **CV Parsing**: PDF text extraction using PyPDF2
✅ **Skill Extraction**: NLP-based skill identification from CV text
✅ **Intelligent Matching**: Algorithm-based task-employee suitability scoring
✅ **Workload Tracking**: Capacity calculation based on active tasks
✅ **Task Management**: Full CRUD operations for tasks
✅ **Role-Based Access**: PM and Employee role separation
✅ **Dashboard Analytics**: Statistics on tasks, capacity, and coverage
✅ **JWT Authentication**: Secure API access
✅ **Async CV Processing**: Background thread processing for CVs

## Technology Stack

- **Django 4.2.7**: Web framework
- **Django REST Framework 3.14.0**: API framework
- **PostgreSQL**: Database (via psycopg2)
- **PyPDF2 3.0.1**: PDF parsing
- **spaCy 3.7.2**: NLP library (installed, can be used for advanced features)
- **NLTK 3.8.1**: Natural language processing
- **PyJWT 2.8.0**: JWT token handling
- **django-cors-headers**: CORS support for frontend

## Database Schema

```
User (Custom)
  ├── Employee (OneToOne)
  │   ├── CV (OneToOne)
  │   └── Skill (ForeignKey)
  │   └── TaskAssignment (ForeignKey)
  │
  └── Task (ForeignKey - created_by)
      ├── TaskSkill (ForeignKey)
      └── TaskAssignment (ForeignKey)
```

## Matching Algorithm Details

The suitability score is calculated as:
```
Score = (SkillMatch × 0.7) + (WorkloadScore × 0.2) + (ExperienceScore × 0.1)
```

Where:
- **SkillMatch**: Ratio of matching skills (0-1)
- **WorkloadScore**: Availability based on current workload (0-1)
- **ExperienceScore**: Average confidence of matching skills (0-1)

## Setup & Deployment

1. Install dependencies: `pip install -r requirements.txt`
2. Configure database in `.env` file
3. Run migrations: `python manage.py migrate`
4. Create demo users: `python manage.py create_demo_users`
5. Start server: `python manage.py runserver`

See `README.md` for detailed setup instructions.

## API Response Format

All API responses follow REST conventions:
- Success: 200/201 with data
- Error: 400/401/404/500 with error message
- Authentication: Bearer token in Authorization header

## Frontend Integration

The backend is designed to work with the existing React frontend:
- Base URL: `http://localhost:8000/api/`
- CORS enabled for `localhost:5173` and `localhost:3000`
- JWT tokens stored in localStorage as `itas_token`
- All endpoints match frontend expectations

## Future Enhancements

Potential improvements:
- Celery for async task processing (instead of threads)
- Advanced NLP with spaCy models
- Portfolio parsing (GitHub, LinkedIn integration)
- Real-time notifications
- Performance metrics and analytics
- Soft skills evaluation
- Learning path recommendations
