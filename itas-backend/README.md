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

- **Python 3.11.x (Recommended)**: It is highly recommended to use Python 3.11. Newer versions (like Python 3.12+) or pre-releases (like Python 3.14+) might not have pre-compiled wheels for scientific dependencies (e.g., `numpy`, `scikit-learn`, `spacy`) on PyPI, which forces `pip` to compile them from source (requiring C++ compilers like MSVC/GCC).
- **PostgreSQL 12+**
- **pip / virtualenv**

> [!TIP]
> **Troubleshooting Windows App Execution Aliases:**
> If running `python` or `setup.bat` displays the message: *"Python was not found; run without arguments to install from the Microsoft Store..."*, you need to disable Windows' default Python aliases. Go to **Settings > Apps > Advanced app settings > App execution aliases** and toggle off **Python** and **Python3**.

### 2. Install Dependencies

**Option A: Using setup script (Recommended)**

**On Windows:**
The setup script will automatically try to locate a Python 3.11 installation using the Python Launcher (`py -3.11`) or direct executable (`python3.11`) to ensure compatibility:
```cmd
cd itas-backend
setup.bat
```

**On Linux/Mac:**
```bash
cd itas-backend
chmod +x setup.sh
./setup.sh
```

**Option B: Manual setup**
```cmd
cd itas-backend
# Force creation using Python 3.11 if multiple versions are installed
py -3.11 -m venv venv  # Or: python3.11 -m venv venv
venv\Scripts\activate  # On Linux/Mac: source venv/bin/activate
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

The matching engine calculates suitability scores (0-100) based on dynamic priority weightings. For a standard "Medium" priority task:

1. **Skill Matching (45% weight)**: How well employee skills match task requirements
2. **Workload Balance (20% weight)**: Employee's current availability
3. **Skill Coverage (15% weight)**: Proportion of required skills the employee possesses
4. **Experience Level (10% weight)**: Confidence scores from skill extraction
5. **Past Performance (10% weight)**: Based on detailed PM ratings (quality, timeliness, communication, technical) on past tasks

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

## Deployment

See `DEPLOYMENT.md` for Render deployment instructions and recommended environment variables (SECRET_KEY, DEBUG=False, DATABASE_URL, etc.).
