from rest_framework import serializers
from .models import DiscoveryPreference, Interest, OccupationCategory, Profile, ProfilePhoto, Province
from .services import age_from_birth_date

class ProvinceSerializer(serializers.ModelSerializer):
    class Meta: model=Province; fields=("code","name")
class OccupationCategorySerializer(serializers.ModelSerializer):
    class Meta: model=OccupationCategory; fields=("id","name")
class InterestSerializer(serializers.ModelSerializer):
    class Meta: model=Interest; fields=("id","name")
class ProfilePhotoSerializer(serializers.ModelSerializer):
    class Meta: model=ProfilePhoto; fields=("id","public_url","thumbnail_url","position","is_primary","width","height","mime_type")

class ProfileWriteSerializer(serializers.ModelSerializer):
    interest_ids=serializers.PrimaryKeyRelatedField(source="interests",queryset=Interest.objects.filter(is_active=True),many=True,required=False)
    class Meta:
        model=Profile
        fields=("display_name","birth_date","gender","interested_genders","current_province","hometown_province","height_cm","occupation_category","occupation_text","education_level","income_band","relationship_status","relationship_goal","religion","smoking_status","drinking_status","children_status","children_plan","bio","looking_for","interest_ids","field_visibility")
    def validate_birth_date(self,value):
        if age_from_birth_date(value)<18: raise serializers.ValidationError("Bạn phải từ 18 tuổi.")
        return value
    def validate_interested_genders(self,value):
        valid={x[0] for x in Profile.Gender.choices}
        if not isinstance(value,list) or not value or any(x not in valid for x in value): raise serializers.ValidationError("Lựa chọn giới tính không hợp lệ.")
        return list(dict.fromkeys(value))
    def validate_interest_ids(self,value):
        if len(value)>10: raise serializers.ValidationError("Chỉ được chọn tối đa 10 sở thích.")
        return value
    def validate_field_visibility(self,value):
        allowed_fields={"income_band","hometown_province","current_province","education_level","religion","smoking_status","drinking_status","children_status","children_plan"}
        allowed_rules={"members","connections","private"}
        if not isinstance(value,dict) or any(k not in allowed_fields or v not in allowed_rules for k,v in value.items()):
            raise serializers.ValidationError("Cấu hình quyền riêng tư không hợp lệ.")
        return value
    def update(self,instance,validated):
        interests=validated.pop("interests",None)
        sensitive_changed=any(k in validated and getattr(instance,k)!=v for k,v in validated.items() if k in {"display_name","birth_date","gender"})
        instance=super().update(instance,validated)
        if interests is not None: instance.interests.set(interests)
        if sensitive_changed and instance.verification_level==Profile.VerificationLevel.IDENTITY:
            instance.verification_level=Profile.VerificationLevel.RECHECK; instance.save(update_fields=["verification_level","updated_at"])
        return instance

class MyProfileSerializer(serializers.ModelSerializer):
    age=serializers.SerializerMethodField(); photos=ProfilePhotoSerializer(many=True,read_only=True); interests=InterestSerializer(many=True,read_only=True)
    current_province=ProvinceSerializer(read_only=True); hometown_province=ProvinceSerializer(read_only=True); occupation_category=OccupationCategorySerializer(read_only=True)
    class Meta:
        model=Profile
        fields=("public_id","display_name","birth_date","age","gender","interested_genders","current_province","hometown_province","height_cm","occupation_category","occupation_text","education_level","income_band","relationship_status","relationship_goal","religion","smoking_status","drinking_status","children_status","children_plan","bio","looking_for","interests","photos","field_visibility","visibility_status","completion_percent","verification_level","verified_at","published_at")
    def get_age(self,obj): return age_from_birth_date(obj.birth_date)

class PublicProfileSerializer(serializers.ModelSerializer):
    age=serializers.SerializerMethodField(); photos=ProfilePhotoSerializer(many=True,read_only=True); interests=InterestSerializer(many=True,read_only=True)
    current_province=ProvinceSerializer(read_only=True); hometown_province=ProvinceSerializer(read_only=True); occupation_category=OccupationCategorySerializer(read_only=True)
    connection_status=serializers.SerializerMethodField()
    class Meta:
        model=Profile
        fields=("public_id","display_name","age","gender","current_province","hometown_province","height_cm","occupation_category","occupation_text","education_level","income_band","relationship_status","relationship_goal","religion","smoking_status","drinking_status","children_status","children_plan","bio","looking_for","interests","photos","verification_level","verified_at","completion_percent","connection_status")
    def get_age(self,obj): return age_from_birth_date(obj.birth_date)
    def get_connection_status(self,obj):
        from apps.connections.services import connection_status_between
        return connection_status_between(self.context["request"].user,obj.user)
    def to_representation(self,instance):
        data=super().to_representation(instance); request=self.context["request"]
        from apps.connections.services import users_are_connected
        connected=users_are_connected(request.user,instance.user)
        visibility=instance.field_visibility or {}
        for field in ["income_band","hometown_province","current_province","education_level","religion","smoking_status","drinking_status","children_status","children_plan"]:
            rule=visibility.get(field,"members")
            if rule=="private" or (rule=="connections" and not connected): data[field]=None
        return data

class DiscoveryPreferenceSerializer(serializers.ModelSerializer):
    class Meta: model=DiscoveryPreference; exclude=("user",)
