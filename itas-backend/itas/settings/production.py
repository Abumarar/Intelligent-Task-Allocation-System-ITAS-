import os

from .base import *

DEBUG = False

if SECRET_KEY == "django-insecure-dev-key-change-in-production":
    raise ValueError("You must set a secure SECRET_KEY in production!")

ALLOWED_HOSTS = [
    "itas-backend-qwtp.onrender.com",
    "www.jobtecacademy.com",
    "jobtecacademy.com",
    "*",
]

render_external_hostname = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if render_external_hostname:
    ALLOWED_HOSTS.append(render_external_hostname)

CORS_ALLOWED_ORIGINS = [
    "https://www.jobtecacademy.com",
    "https://jobtecacademy.com",
    "https://itas-frontend.vercel.app",
]

CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS

# Security Headers
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Redis Caching for Production (Fallback to LocMem if REDIS_URL not provided)
REDIS_URL = os.getenv("REDIS_URL")
if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }
