"""
WSGI config for itas project.
"""

import os

from django.core.wsgi import get_wsgi_application

settings_module = "itas.settings.production" if os.environ.get("RENDER") else "itas.settings.development"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)

application = get_wsgi_application()
