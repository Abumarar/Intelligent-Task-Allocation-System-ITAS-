"""
URL configuration for itas project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.http import JsonResponse
import os

def home(request):
    return JsonResponse({"message": "ITAS Backend API is running", "status": "ok"})

def debug_media(request):
    """Debug view to check media file existence."""
    media_root = settings.MEDIA_ROOT
    media_url = settings.MEDIA_URL
    path = request.GET.get('path', '')
    
    exists = False
    full_path = ""
    folder_contents = []
    
    if path:
        full_path = os.path.join(media_root, path)
        exists = os.path.exists(full_path)
    
    # List media root contents
    try:
        if os.path.exists(media_root):
            folder_contents = os.listdir(media_root)
            # Check subfolders like 'cvs'
            cvs_path = os.path.join(media_root, 'cvs')
            if os.path.exists(cvs_path):
                folder_contents.extend([f"cvs/{f}" for f in os.listdir(cvs_path)])
        else:
            folder_contents = ["Media Root does not exist"]
    except Exception as e:
        folder_contents = [str(e)]

    return JsonResponse({
        "MEDIA_ROOT": media_root,
        "MEDIA_URL": media_url,
        "Requested Path": path,
        "Full Path": full_path,
        "Exists": exists,
        "Folder Contents": folder_contents,
        "DEBUG": settings.DEBUG,
        "Service": "ITAS Backend"
    })

urlpatterns = [
    path('debug-media/', debug_media),
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    path('', home),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Serve media in production for demo purposes (usually handled by Nginx/S3)
    # This captures everything under /media/
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
