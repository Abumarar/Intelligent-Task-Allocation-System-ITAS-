import os

# Gunicorn configuration for Render
# Render sets the PORT environment variable
port = os.getenv("PORT", "10000")
bind = f"0.0.0.0:{port}"

# Worker configuration
workers = 2
threads = 4
timeout = 120
accesslog = "-"
errorlog = "-"
loglevel = "info"
