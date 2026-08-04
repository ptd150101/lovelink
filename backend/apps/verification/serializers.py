from rest_framework import serializers
from .models import VerificationRequest,VerificationEvidence,VerificationReview
class EvidenceSerializer(serializers.ModelSerializer):
 class Meta:model=VerificationEvidence;fields=("id","evidence_type","mime_type","file_size","uploaded_at","deleted_at")
class VerificationRequestSerializer(serializers.ModelSerializer):
 evidence=EvidenceSerializer(many=True,read_only=True)
 class Meta:model=VerificationRequest;fields=("id","status","challenge_code","submitted_at","review_started_at","decided_at","decision_reason_code","user_visible_reason","expires_at","evidence","created_at","updated_at")
class StaffVerificationSerializer(VerificationRequestSerializer):
 user=serializers.SerializerMethodField()
 class Meta(VerificationRequestSerializer.Meta):fields=VerificationRequestSerializer.Meta.fields+("user",)
 def get_user(self,obj):return {"id":str(obj.user_id),"email":obj.user.email,"public_id":str(obj.user.profile.public_id),"display_name":obj.user.profile.display_name,"photos":[x.public_url for x in obj.user.profile.photos.all()]}
