Render deployment checklist

This file contains steps and environment variable suggestions to deploy the backend to Render (https://render.com).

Required environment variables (set in Render service settings):
- SECRET_KEY: your Django secret key (required)
- DEBUG: False
- DJANGO_SETTINGS_MODULE: itas.settings (default)
- DATABASE_URL: Postgres connection string if using a managed DB (recommended)
- JWT_SECRET_KEY: secret for JWT tokens (optional, defaults to SECRET_KEY)
- ALLOWED_HOSTS: or use the built-in ALLOWED_HOSTS configuration that includes .onrender.com and your domain
- SECURE_SSL_REDIRECT: True (optional, default enabled when DEBUG=False)

Quick deploy steps:
1. Add repository to Render and create a Web Service.
2. Environment: Python 3.x
3. Build Command: pip install -r requirements.txt && ./build.sh
4. Start Command: gunicorn itas.wsgi --log-file -
5. Add release command (or use a render.yaml) to run migrations and collectstatic before starting the service (or rely on `./build.sh`):
   - python manage.py migrate --noinput
   - python manage.py collectstatic --noinput
6. Set environment variables in Render as listed above.
7. (Optional) Configure a custom domain on Render (e.g., api.jobtecacademy.com or jobtecacademy.com) and make sure DNS is pointed correctly.

Notes & recommendations
- Media files: Consider using managed object storage (e.g., AWS S3 or DigitalOcean Spaces) for MEDIA files in production. WhiteNoise only serves STATIC files.
- Ensure SECRET_KEY is not left as the development default.
- For improved security, configure the following in the Render environment as needed: SECURE_HSTS_SECONDS, SECURE_SSL_REDIRECT
