"""
URL routing for core app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from core.views import AuthView, EmployeeViewSet, TaskViewSet, DashboardView, seed_db

router = DefaultRouter()
router.register(r'employees', EmployeeViewSet, basename='employee')
router.register(r'tasks', TaskViewSet, basename='task')
# Note: my-profile endpoint is added via @action decorator in TaskViewSet

@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    """API root endpoint showing available endpoints."""
    return Response({
        'message': 'ITAS API',
        'endpoints': {
            'auth': {
                'login': '/api/auth/login (POST) - No authentication required'
            },
            'employees': '/api/employees/ - Requires authentication',
            'tasks': '/api/tasks/ - Requires authentication',
            'dashboard': '/api/dashboard/stats - Requires authentication'
        },
        'info': 'Use /api/auth/login to get a JWT token for authenticated requests'
    })

urlpatterns = [
    path('', api_root, name='api-root'),
    path('auth/login', AuthView.as_view(), name='auth-login'),
    path('seed', seed_db, name='seed-db'),
    path('dashboard/stats', DashboardView.as_view(), name='dashboard-stats'),
    path('', include(router.urls)),
]
