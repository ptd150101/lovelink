from rest_framework import serializers
from apps.connections.serializers import CompactUserSerializer
from .models import CallSession
class CallSessionSerializer(serializers.ModelSerializer):
 caller_user_id=serializers.UUIDField(source="caller_id",read_only=True);callee_user_id=serializers.UUIDField(source="callee_id",read_only=True)
 caller=CompactUserSerializer(read_only=True);callee=CompactUserSerializer(read_only=True)
 class Meta:model=CallSession;fields=("id","room_name","caller_user_id","callee_user_id","caller","callee","conversation","call_type","status","created_at","ringing_at","accepted_at","connected_at","ended_at","end_reason")
