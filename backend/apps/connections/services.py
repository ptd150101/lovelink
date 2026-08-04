from django.db.models import Q
from .models import ConnectionRequest

def users_are_connected(a,b):
    if not getattr(a,"is_authenticated",False) or not b:return False
    return ConnectionRequest.objects.filter(status=ConnectionRequest.Status.ACCEPTED).filter(Q(sender=a,receiver=b)|Q(sender=b,receiver=a)).exists()

def connection_status_between(a,b):
    if not getattr(a,"is_authenticated",False):return None
    req=ConnectionRequest.objects.filter(Q(sender=a,receiver=b)|Q(sender=b,receiver=a)).order_by("-sent_at").first()
    if not req:return "none"
    direction="sent" if req.sender_id==a.id else "received"
    return f"{direction}_{req.status}"

def accepted_connection(a,b):
    return ConnectionRequest.objects.filter(status=ConnectionRequest.Status.ACCEPTED).filter(Q(sender=a,receiver=b)|Q(sender=b,receiver=a)).first()
