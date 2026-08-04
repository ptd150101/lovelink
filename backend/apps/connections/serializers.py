from rest_framework import serializers

from apps.profiles.serializers import ProfilePhotoSerializer
from apps.profiles.services import presence_for_viewer

from .models import ConnectionRequest


class CompactUserSerializer(serializers.Serializer):
    public_id = serializers.UUIDField(source="profile.public_id")
    display_name = serializers.CharField(source="profile.display_name")
    verification_level = serializers.CharField(source="profile.verification_level")
    is_phone_verified = serializers.BooleanField()
    primary_photo = serializers.SerializerMethodField()
    presence = serializers.SerializerMethodField()

    def get_primary_photo(self, obj):
        photo = (
            obj.profile.photos.filter(is_primary=True).first()
            or obj.profile.photos.first()
        )
        return ProfilePhotoSerializer(photo).data if photo else None

    def get_presence(self, obj):
        request = self.context.get("request")
        return presence_for_viewer(obj, request.user) if request else None


class ConnectionRequestSerializer(serializers.ModelSerializer):
    sender = CompactUserSerializer(read_only=True)
    receiver = CompactUserSerializer(read_only=True)
    other_user = serializers.SerializerMethodField()

    class Meta:
        model = ConnectionRequest
        fields = (
            "id",
            "sender",
            "receiver",
            "other_user",
            "intro_message",
            "status",
            "sent_at",
            "responded_at",
            "expires_at",
        )

    def get_other_user(self, obj):
        request = self.context.get("request")
        if not request:
            return None
        other = obj.receiver if obj.sender_id == request.user.id else obj.sender
        return CompactUserSerializer(other, context=self.context).data
