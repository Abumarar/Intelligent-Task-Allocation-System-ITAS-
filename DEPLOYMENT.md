# Production Deployment Guide

This guide covers the deployment process for the Intelligent Task Allocation System (ITAS).

## Production Checklist

Before deploying to production, ensure the following:
- [ ] `DEBUG=False` in backend `.env`
- [ ] `SECRET_KEY` is a strong, random value and not shared
- [ ] Database credentials are secure and IP restricted
- [ ] CORS headers are restrictive (remove `*` from `CORS_ALLOWED_ORIGINS`)
- [ ] HTTPS is enforced (`SECURE_SSL_REDIRECT=True`)

## Architecture Setup

1. **Backend**: Deploy the Django app using Gunicorn and Nginx.
2. **Frontend**: Build static assets and serve via Vercel, Netlify, or Nginx.
3. **Database**: Managed PostgreSQL instance (e.g., AWS RDS, Supabase).
4. **Cache/Queue**: Managed Redis instance for Celery tasks.

## Rollback Procedures

If a deployment fails:
1. Revert to the previous Docker image tag or git commit.
2. If database migrations were applied, run `python manage.py migrate <app_name> <previous_migration_name>`.
3. Monitor the `/api/health/` endpoint to confirm the rollback was successful.

## Monitoring

Please refer to [MONITORING.md](docs/MONITORING.md) for details on setting up Prometheus, Grafana, and Sentry for error tracking.
