#!/usr/bin/env bash
# Exit on error
set -o errexit

# Modify this line as needed for your package manager (pip, poetry, etc.)
pip install -r requirements.txt

# Download NLTK data
python -m nltk.downloader punkt averaged_perceptron_tagger maxent_ne_chunker words

# Ensure spaCy model linking if needed (though direct install usually works)
python -m spacy download en_core_web_sm || true

# Convert static asset files
python manage.py collectstatic --no-input

# Apply any outstanding database migrations
python manage.py migrate

# Create test users (for demo)
python manage.py create_test_users
