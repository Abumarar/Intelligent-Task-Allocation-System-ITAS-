# Development Guide

Welcome to the ITAS development guide. Here you will find instructions to set up your local environment and contribute code.

## Prerequisites

- Python 3.10+
- Node.js 18+
- Git

## Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd itas-backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run migrations:
   ```bash
   python manage.py migrate
   ```
5. Run the development server:
   ```bash
   python manage.py runserver
   ```

## Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd itas-frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the Vite dev server:
   ```bash
   npm run dev
   ```

## Pre-commit Hooks

To ensure code quality, we use `pre-commit` to run formatting and linting automatically before every commit.

1. Ensure `pre-commit` is installed globally or in your virtual environment:
   ```bash
   pip install pre-commit
   ```
2. Install the hooks from the root of the project:
   ```bash
   pre-commit install
   ```

## Running Tests

- **Backend**: `pytest`
- **Frontend**: `npm run test`
