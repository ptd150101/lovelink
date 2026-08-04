from datetime import date
from django.utils import timezone
from .models import Profile

REQUIRED_FIELDS=("display_name","gender","interested_genders","current_province_id","hometown_province_id","height_cm","occupation_category_id","occupation_text","education_level","relationship_status","relationship_goal","bio")

def age_from_birth_date(birth_date):
    today=date.today(); return today.year-birth_date.year-((today.month,today.day)<(birth_date.month,birth_date.day))

def profile_completion(profile):
    score=sum(bool(getattr(profile,f)) for f in REQUIRED_FIELDS)
    score += bool(profile.looking_for)+bool(profile.interests.exists())+bool(profile.photos.exists())
    return round(score/(len(REQUIRED_FIELDS)+3)*100)

def validate_publish(profile):
    errors={}
    for field in REQUIRED_FIELDS:
        if not getattr(profile,field): errors[field]="Trường này là bắt buộc."
    if age_from_birth_date(profile.birth_date)<18: errors["birth_date"]="Bạn phải từ 18 tuổi."
    if not profile.photos.filter(moderation_status="approved").exists(): errors["photos"]="Cần ít nhất một ảnh."
    if len(profile.bio.strip())<50: errors["bio"]="Giới thiệu cần ít nhất 50 ký tự."
    return errors

def publish(profile):
    errors=validate_publish(profile)
    if errors: return errors
    profile.completion_percent=profile_completion(profile); profile.visibility_status=Profile.Visibility.PUBLISHED
    profile.published_at=profile.published_at or timezone.now(); profile.save(update_fields=["completion_percent","visibility_status","published_at","updated_at"])
    return {}


def require_verification_recheck(profile):
    if profile.verification_level == Profile.VerificationLevel.IDENTITY:
        profile.verification_level = Profile.VerificationLevel.RECHECK
        profile.verified_at = None
        profile.save(update_fields=["verification_level", "verified_at", "updated_at"])
