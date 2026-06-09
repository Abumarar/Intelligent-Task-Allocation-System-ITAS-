from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from core.services.email_service import EmailService

@api_view(["GET"])
@permission_classes([AllowAny])
def debug_media(request):
    """Debug endpoint for checking media setups."""
    return JsonResponse({"status": "ok", "message": "Media debug endpoint works."})

@api_view(["GET"])
@permission_classes([AllowAny])
def debug_email(request):
    """Debug endpoint for testing email sending configuration."""
    recipient = request.GET.get("recipient")
    
    if not recipient:
        return JsonResponse({"status": "error", "message": "Please provide a ?recipient=email parameter"}, status=400)
        
    try:
        EmailService.send_email(
            subject="ITAS Debug Email Test",
            message="This is a test email from the ITAS application to verify SMTP configuration.",
            recipient_list=[recipient]
        )
        return JsonResponse({"status": "ok", "message": f"Test email queued for {recipient}"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
