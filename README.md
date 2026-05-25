# Intelligent Task Allocation System (ITAS)

**Live Demo:** [https://www.jobtecacademy.com/](https://www.jobtecacademy.com/)

![Status: In Progress](https://img.shields.io/badge/status-in%20progress-yellow)
![Tech Stack](https://img.shields.io/badge/tech-Python%2C%20Django-blue)
![Database](https://img.shields.io/badge/database-PostgreSQL-green)

## Project Overview
ITAS is a web-based system designed to optimize software development task allocation within IT projects. It ensures fair, data-driven assignment by analyzing employees’ CVs and portfolios, matching them with task requirements.

## Problem Statement
- Manual task assignment is biased and inefficient.
- Project Managers often lack visibility into full team skill sets.
- Fresh graduates are often overlooked despite relevant skills.

## Proposed Solution
1. Employees upload CVs (PDF/Docx) and portfolio links (GitHub/Behance).  
2. NLP and RegEx parsing extract technical skills.  
3. Project Managers create tasks with skill tags.  
4. Matching engine calculates suitability scores for each employee.  
5. Dashboard visualizes workload and task progress.  
6. Feedback loop updates employee scores based on performance.

## Core Features
- **Profile Parser:** Extracts and analyzes CV and portfolio data.  
- **Task Manager:** Task creation and skill tagging.  
- **Matching Engine:** Calculates suitability scores with dual-stream logic for fresh vs senior employees.  
- **Dashboard:** Shows employee workload and task completion.  
- **Feedback Loop & Performance Rating:** Detailed PM feedback on completed tasks updates employee suitability scores dynamically.

## Visual Overview

### Project Manager Interface

#### PM Dashboard
![PM Dashboard](docs/screenshots/dashboard.png)

#### Talent Directory (CV Parsing)
![Employees](docs/screenshots/employees.png)

#### System Reports & Analytics
![Reports](docs/screenshots/reports.png)

#### Project Portfolio
![Projects](docs/screenshots/projects.png)

### Employee Interface

#### My Profile & Workload
![Employee Dashboard](docs/screenshots/employee_dashboard.png)

#### Personal Settings
![Employee Settings](docs/screenshots/employee_settings.png)

## Project Scope
**Included:**
- CV and portfolio parsing
- NLP-based skill identification
- Task creation with skill tags
- Algorithmic matching and scoring (incorporating past performance)
- Dashboard for project managers
- Employee profile management
- Detailed PM rating system for completed tasks

**Excluded:**
- Soft skills evaluation
- Full integration with external HR systems
- Real-time monitoring of coding performance
- Mobile application

## Technical Stack
- **Frontend:** React.js or Vue.js  
- **Backend:** Python (Django or Flask)  
- **Database:** PostgreSQL  
- **Text Processing:** PyPDF2, NLTK / spaCy

## Quick Start (Windows)

To get both the frontend and backend running locally on a Windows machine:

1. **Clone the repository:**
   ```cmd
   git clone <repository-url>
   cd "Intelligent Task Allocation System (ITAS)"
   ```

2. **Setup the Backend:**
   ```cmd
   cd itas-backend
   setup.bat
   ```
   *(This will create the virtual environment, install dependencies, and create the `.env` file.)*
   
   > [!IMPORTANT]
   > **Python Version & Windows Aliases:** 
   > - It is highly recommended to have **Python 3.11** installed.
   > - If you receive a *"Python was not found"* error, turn off Windows Python aliases in **Settings > Apps > Advanced app settings > App execution aliases** (toggle off **Python** and **Python3**).

3. **Start the Backend Server:**
   ```cmd
   :: Make sure your virtual environment is activated
   venv\Scripts\activate
   python manage.py runserver
   ```
   *(The API will be available at `http://localhost:8000/api/`)*

4. **Setup and Start the Frontend:**
   Open a new terminal window:
   ```cmd
   cd "Intelligent Task Allocation System (ITAS)\itas-frontend"
   npm install
   npm run dev
   ```
   *(The app will be available at `http://localhost:5173`)*

## Cloud Deployment (Production)

This project uses a modern decoupled architecture:
- **Database:** Supabase (PostgreSQL)
- **Backend API:** Render (Django)
- **Frontend:** Vercel (React)

### 1. Database (Supabase)
1. Create a project on [Supabase](https://supabase.com).
2. Go to **Project Settings -> Database** and copy your **Connection String (URI)**.
3. Keep the password you created safe.

### 2. Backend API (Render)
1. Push your `itas-backend` code to GitHub.
2. In [Render](https://render.com), create a new **Web Service** connected to your repo.
3. Configure the following build settings:
   - **Root Directory:** `itas-backend`
   - **Build Command:** `./build.sh`
   - **Start Command:** `gunicorn itas.wsgi:application`
4. Set the following **Environment Variables**:
   - `DATABASE_URL`: Your Supabase connection URI (e.g., `postgresql://postgres...`)
   - `SECRET_KEY`: A secure random string for Django
   - `DEBUG`: `False`
   - `JWT_SECRET_KEY`: A secure key for tokens

### 3. Frontend (Vercel)
1. Push your `itas-frontend` code to GitHub.
2. In [Vercel](https://vercel.com), import the repository.
3. Ensure the Framework Preset is set to **Vite** or **React**.
4. Set the **Root Directory** to `itas-frontend`.
5. Set the **Environment Variable**:
   - `VITE_API_BASE_URL`: `https://<your-render-app-url>.onrender.com/api`
6. Deploy!

## References
- Jira Smart Assignment and Automation Tools  
- GitHub Projects & Actions  
- NLP-Based Applicant Tracking Systems (ATS)  
- Smart Hiring & CV Matching Systems  
- Competency Profiling & Skill Management Systems  
- [Scholar References](https://scholar.google.com/scholar?q=Coordinating+expertise+in+software+development+teams)
