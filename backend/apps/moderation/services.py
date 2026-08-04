from django.db.models import Q
from .models import Block

def are_blocked(a,b):return Block.objects.filter(Q(blocker=a,blocked=b)|Q(blocker=b,blocked=a)).exists()
def blocked_user_ids(user):
    ids=set()
    for blocker_id,blocked_id in Block.objects.filter(Q(blocker=user)|Q(blocked=user)).values_list("blocker_id","blocked_id"):
        ids.add(blocked_id if blocker_id==user.id else blocker_id)
    return ids
