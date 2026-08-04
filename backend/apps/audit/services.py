from .context import request_context
from .models import AuditLog

def audit(*, actor, action, target, before=None, after=None, actor_role=""):
    ctx = request_context.get()
    return AuditLog.objects.create(
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        actor_role=actor_role or ("superuser" if getattr(actor, "is_superuser", False) else "staff" if getattr(actor, "is_staff", False) else "member"),
        action=action,
        target_type=target.__class__.__name__,
        target_id=str(target.pk),
        before_data=before or {},
        after_data=after or {},
        ip_address=ctx.get("ip_address"),
        user_agent=ctx.get("user_agent", ""),
    )
