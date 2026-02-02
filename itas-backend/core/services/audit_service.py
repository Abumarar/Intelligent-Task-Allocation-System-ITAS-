from core.models import AuditLog

class AuditService:
    @staticmethod
    def log(user, action, target, details=None, ip_address=None):
        """
        Log an action to the audit log.
        
        Args:
            user: User performing the action
            action: Action type (CREATE, UPDATE, DELETE, etc.)
            target: The model instance being targeted
            details: Optional text details
            ip_address: Optional IP address
        """
        try:
            target_model = target._meta.model_name
            target_id = str(target.id)
        except AttributeError:
            target_model = str(target)
            target_id = None

        AuditLog.objects.create(
            user=user,
            action=action,
            target_model=target_model,
            target_id=target_id,
            details=details,
            ip_address=ip_address
        )
