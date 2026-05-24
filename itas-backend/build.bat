@echo off
:: Exit on error
setlocal enabledelayedexpansion

:: Modify this line as needed for your package manager (pip, poetry, etc.)
pip install -r requirements.txt
if %errorlevel% neq 0 exit /b %errorlevel%

:: Download NLTK data
python -m nltk.downloader punkt averaged_perceptron_tagger maxent_ne_chunker words
if %errorlevel% neq 0 exit /b %errorlevel%

:: Ensure spaCy model linking if needed (though direct install usually works)
python -m spacy download en_core_web_sm

:: Convert static asset files
python manage.py collectstatic --no-input
if %errorlevel% neq 0 exit /b %errorlevel%

:: Train AI Model (using Kaggle Dataset)
python ai_training\train_model.py
if %errorlevel% neq 0 exit /b %errorlevel%

:: Apply any outstanding database migrations
python manage.py migrate
if %errorlevel% neq 0 exit /b %errorlevel%

:: Create test users (for demo)
python manage.py create_test_users
if %errorlevel% neq 0 exit /b %errorlevel%
