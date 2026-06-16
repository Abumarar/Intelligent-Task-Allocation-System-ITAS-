# Architecture Overview

The Intelligent Task Allocation System (ITAS) is a full-stack application designed to automatically allocate tasks to employees based on their CVs and skill sets.

## System Architecture

ITAS uses a standard 3-tier architecture:
1. **Frontend (Presentation Tier)**: React/TypeScript via Vite.
2. **Backend (Application Tier)**: Django REST Framework (Python).
3. **Database (Data Tier)**: SQLite (Development) / PostgreSQL (Production).
4. **Machine Learning Engine**: Integrated into the backend via `joblib`/`scikit-learn`.

## Data Flow

1. **User Management**: PMs and Employees are registered in the system.
2. **CV Upload**: An employee uploads a PDF or DOCX CV.
3. **Parsing & Extraction**: The backend uses PyPDF2/python-docx to extract text, and an ML model (or regex heuristics) to extract skills.
4. **Task Creation**: A Project Manager creates a task with specific requirements.
5. **Matching Engine**: The system calculates a suitability score for each employee against the task based on extracted skills.
6. **Allocation**: Tasks are allocated to the best-fit employees.

## Key Components

- **Frontend**: `itas-frontend/src/`
  - React Query for data fetching.
  - TailwindCSS for styling.
- **Backend**: `itas-backend/`
  - `core/models.py`: Database schema definition.
  - `core/services/cv_parser.py`: Extracts text from documents.
  - `core/services/skill_extractor.py`: Extracts skills from text.
  - `core/services/matching_engine.py`: Matches skills to tasks.
- **ML Pipeline**: `itas-backend/ai_training/`
  - Used to train models on historical task allocation data.
