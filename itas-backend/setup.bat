@echo off
echo Setting up ITAS Backend...

:: Create virtual environment if it doesn't exist
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

:: Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

:: Install dependencies
echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

:: Download NLTK data (if needed)
echo Downloading NLTK data...
python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('averaged_perceptron_tagger', quiet=True); nltk.download('maxent_ne_chunker', quiet=True); nltk.download('words', quiet=True)"

:: Generate random secrets using Python
for /f "tokens=*" %%a in ('python -c "import secrets; print(secrets.token_hex(32))"') do set SECRET_KEY=%%a
for /f "tokens=*" %%a in ('python -c "import secrets; print(secrets.token_hex(32))"') do set JWT_SECRET_KEY=%%a

:: Create .env file if it doesn't exist
if not exist .env (
    echo Creating .env file from template...
    echo SECRET_KEY=django-insecure-dev-key-%SECRET_KEY%> .env
    echo DEBUG=True>> .env
    echo DB_NAME=itas_db>> .env
    echo DB_USER=postgres>> .env
    echo DB_PASSWORD=postgres>> .env
    echo DB_HOST=localhost>> .env
    echo DB_PORT=5432>> .env
    echo JWT_SECRET_KEY=jwt-secret-%JWT_SECRET_KEY%>> .env
    echo .env file created. Please update database credentials if needed.
)

:: Run migrations
echo Running migrations...
python manage.py makemigrations
python manage.py migrate

:: Create demo users
echo Creating demo users...
python manage.py create_demo_users

echo.
echo Setup complete!
echo.
echo Next steps:
echo 1. Update .env file with your database credentials
echo 2. Create a superuser: python manage.py createsuperuser
echo 3. Run the server: python manage.py runserver
echo.
echo Demo users created:
echo   PM: pm@itas.com / pm123
echo   Employee: employee@itas.com / emp123
