from django.http import JsonResponse
from django.conf import settings
import os

def debug_media(request):
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
        folder_contents = os.listdir(media_root)
        # Check subfolders like 'cvs'
        cvs_path = os.path.join(media_root, 'cvs')
        if os.path.exists(cvs_path):
            folder_contents.extend([f"cvs/{f}" for f in os.listdir(cvs_path)])
    except Exception as e:
        folder_contents = [str(e)]

    return JsonResponse({
        "MEDIA_ROOT": media_root,
        "MEDIA_URL": media_url,
        "Requested Path": path,
        "Full Path": full_path,
        "Exists": exists,
        "Folder Contents": folder_contents,
        "DEBUG": settings.DEBUG
    })
