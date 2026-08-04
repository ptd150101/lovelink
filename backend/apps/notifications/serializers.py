from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    actor = serializers.SerializerMethodField()
    class Meta:
        model = Notification
        fields = ("id", "type", "actor", "entity_type", "entity_id", "title", "body", "read_at", "created_at")
    def get_actor(self, obj):
        if not obj.actor_id: return None
        profile = getattr(obj.actor, "profile", None)
        return {"public_id": str(getattr(profile, "public_id", "")), "display_name": getattr(profile, "display_name", "")}
