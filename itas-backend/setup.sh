#!/bin/bash
# Setup script for ITAS Backend

echo "Setting up ITAS Backend..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Download NLTK data (if needed)
echo "Downloading NLTK data..."
python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('averaged_perceptron_tagger', quiet=True); nltk.download('maxent_ne_chunker', quiet=True); nltk.download('words', quiet=True)"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cat > .env << EOF
SECRET_KEY=django-insecure-dev-key-$(openssl rand -hex 32)
DEBUG=True
DB_NAME=itas_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
JWT_SECRET_KEY=jwt-secret-$(openssl rand -hex 32)
EOF
    echo ".env file created. Please update database credentials if needed."
fi

# Run migrations
echo "Running migrations..."
python manage.py makemigrations
python manage.py migrate

# Create demo users
echo "Creating demo users..."
python manage.py create_demo_users

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env file with your database credentials"
echo "2. Create a superuser: python manage.py createsuperuser"
echo "3. Run the server: python manage.py runserver"
echo ""
echo "Demo users created:"
echo "  PM: pm@itas.com / pm123"
echo "  Employee: employee@itas.com / emp123"
