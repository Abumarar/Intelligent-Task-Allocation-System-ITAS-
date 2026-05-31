import os

# Gunicorn configuration for Render
# Render sets the PORT environment variable
port = os.getenv("PORT", "10000")
bind = f"0.0.0.0:{port}"

# Worker configuration optimized for low-memory environments (Render Free Tier)
workers = 1
threads = 2
timeout = 120
preload_app = True
accesslog = "-"
errorlog = "-"
loglevel = "info"
