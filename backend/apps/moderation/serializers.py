from rest_framework import serializers
from .models import Block,Report,ModerationAction
class BlockSerializer(serializers.ModelSerializer):
 public_id=serializers.UUIDField(source="blocked.profile.public_id",read_only=True);display_name=serializers.CharField(source="blocked.profile.display_name",read_only=True)
 class Meta:model=Block;fields=("public_id","display_name","created_at")
class ReportSerializer(serializers.ModelSerializer):
 class Meta:model=Report;fields=("id","reported_user","target_type","target_id","reason_code","description","status","created_at","resolved_at");read_only_fields=("reported_user","status","resolved_at")
class ModerationActionSerializer(serializers.ModelSerializer):
 class Meta:model=ModerationAction;fields="__all__";read_only_fields=("moderator",)
