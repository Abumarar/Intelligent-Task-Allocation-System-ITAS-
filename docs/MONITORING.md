# Monitoring and Observability Guide

## Key Metrics to Monitor

### 1. API Health & Performance
- **HTTP Error Rates** (4xx, 5xx): Alert if > 2% for 5 minutes.
- **Latency**: P95 response times. Alert if > 1s for standard endpoints, > 5s for ML endpoints.
- **Request Rate**: Sudden drops indicate a network or load balancer issue.

### 2. Machine Learning Engine
- **Model Load Time**: Ensure models aren't reloading on every request.
- **Inference Time**: Average time to parse CV or match tasks.
- **Prediction Drift**: Watch for drops in average prediction confidence over time.

### 3. Background Tasks (Celery)
- **Queue Length**: If queue size > 50, workers might be dead or too slow.
- **Task Failure Rate**: Monitor failed tasks for CV parsing or email sending.

## Prometheus Metrics

The backend exposes metrics via `django-prometheus`. Key metrics include:
- `django_http_requests_total_by_method_total`
- `django_http_responses_before_middlewares_total`
- `django_db_query_duration_seconds`

## Sentry Integration

Sentry is used for catching unhandled exceptions in the backend and frontend.
- Configure `SENTRY_DSN` in both `.env` files.
- Watch for "New Issues" and regression alerts in the Sentry dashboard.

## Health Check Endpoint

Use `/api/health/` for load balancer health checks. It verifies:
- Database connectivity
- Redis/Celery connectivity (if enabled)
- General application state
