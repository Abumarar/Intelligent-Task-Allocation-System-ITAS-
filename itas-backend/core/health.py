import time

from django.db import connection
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint for load balancers and monitoring.
    Verifies DB connectivity and basic application state.
    """
    status = "ok"
    components = {"database": "ok", "api": "ok"}

    # Check Database Connectivity
    try:
        connection.ensure_connection()
    except Exception as e:
        status = "degraded"
        components["database"] = "down"

    return JsonResponse(
        {"status": status, "components": components, "timestamp": time.time()},
        status=200 if status == "ok" else 503,
    )
