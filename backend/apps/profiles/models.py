import uuid
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

class Province(models.Model):
    code=models.CharField(max_length=10,primary_key=True)
    name=models.CharField(max_length=100)
    sort_order=models.PositiveSmallIntegerField(default=0)
    class Meta: ordering=("sort_order","name")
    def __str__(self): return self.name

class OccupationCategory(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    name=models.CharField(max_length=120,unique=True)
    is_active=models.BooleanField(default=True)
    def __str__(self): return self.name

class Interest(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    name=models.CharField(max_length=80,unique=True)
    is_active=models.BooleanField(default=True)
    def __str__(self): return self.name

class Profile(models.Model):
    class Gender(models.TextChoices):
        MALE="male","Nam"; FEMALE="female","Nữ"; NON_BINARY="non_binary","Phi nhị nguyên"; OTHER="other","Khác"
    class RelationshipStatus(models.TextChoices):
        SINGLE="single","Độc thân"; DIVORCED="divorced","Đã ly hôn"; WIDOWED="widowed","Góa"
    class Goal(models.TextChoices):
        FRIENDSHIP="friendship","Làm quen"; SERIOUS="serious","Tìm hiểu nghiêm túc"; LONG_TERM="long_term","Hẹn hò lâu dài"; MARRIAGE="marriage","Hướng tới kết hôn"
    class Education(models.TextChoices):
        HIGH_SCHOOL="high_school","THPT"; COLLEGE="college","Cao đẳng"; UNIVERSITY="university","Đại học"; POSTGRADUATE="postgraduate","Sau đại học"; OTHER="other","Khác"
    class Income(models.TextChoices):
        UNDER_10="under_10","Dưới 10 triệu"; FROM_10_20="10_20","10–20 triệu"; FROM_20_30="20_30","20–30 triệu"; FROM_30_50="30_50","30–50 triệu"; FROM_50_100="50_100","50–100 triệu"; ABOVE_100="above_100","Trên 100 triệu"; PRIVATE="private","Không muốn công khai"
    class Habit(models.TextChoices):
        NEVER="never","Không"; SOMETIMES="sometimes","Thỉnh thoảng"; OFTEN="often","Thường xuyên"; PRIVATE="private","Không muốn nói"
    class Children(models.TextChoices):
        NONE="none","Chưa có"; HAS="has","Đã có"; PRIVATE="private","Không muốn nói"
    class ChildrenPlan(models.TextChoices):
        WANT="want","Muốn có"; NOT_WANT="not_want","Không muốn"; UNSURE="unsure","Chưa quyết định"; PRIVATE="private","Không muốn nói"
    class Visibility(models.TextChoices):
        DRAFT="draft","Bản nháp"; PUBLISHED="published","Công khai"; HIDDEN_USER="hidden_by_user","Người dùng ẩn"; HIDDEN_MOD="hidden_by_moderator","Kiểm duyệt ẩn"; SUSPENDED="suspended","Đình chỉ"; DELETED="deleted","Đã xóa"
    class VerificationLevel(models.TextChoices):
        NONE="none","Chưa xác minh"; IDENTITY="identity_verified","Đã xác minh danh tính"; RECHECK="recheck_required","Cần xác minh lại"; REVOKED="revoked","Đã thu hồi"

    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    public_id=models.UUIDField(default=uuid.uuid4,unique=True,editable=False,db_index=True)
    user=models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="profile")
    display_name=models.CharField(max_length=80,blank=True)
    birth_date=models.DateField(db_index=True)
    gender=models.CharField(max_length=24,choices=Gender.choices,blank=True,db_index=True)
    interested_genders=models.JSONField(default=list,blank=True)
    current_province=models.ForeignKey(Province,null=True,blank=True,on_delete=models.SET_NULL,related_name="resident_profiles")
    hometown_province=models.ForeignKey(Province,null=True,blank=True,on_delete=models.SET_NULL,related_name="hometown_profiles")
    height_cm=models.PositiveSmallIntegerField(null=True,blank=True,validators=[MinValueValidator(120),MaxValueValidator(230)],db_index=True)
    occupation_category=models.ForeignKey(OccupationCategory,null=True,blank=True,on_delete=models.SET_NULL,related_name="profiles")
    occupation_text=models.CharField(max_length=160,blank=True)
    education_level=models.CharField(max_length=32,choices=Education.choices,blank=True,db_index=True)
    income_band=models.CharField(max_length=24,choices=Income.choices,blank=True,db_index=True)
    relationship_status=models.CharField(max_length=24,choices=RelationshipStatus.choices,blank=True)
    relationship_goal=models.CharField(max_length=24,choices=Goal.choices,blank=True,db_index=True)
    religion=models.CharField(max_length=100,blank=True)
    smoking_status=models.CharField(max_length=20,choices=Habit.choices,blank=True)
    drinking_status=models.CharField(max_length=20,choices=Habit.choices,blank=True)
    children_status=models.CharField(max_length=20,choices=Children.choices,blank=True)
    children_plan=models.CharField(max_length=20,choices=ChildrenPlan.choices,blank=True)
    bio=models.TextField(blank=True,max_length=1500)
    looking_for=models.TextField(blank=True,max_length=1000)
    interests=models.ManyToManyField(Interest,blank=True,related_name="profiles")
    field_visibility=models.JSONField(default=dict,blank=True)
    visibility_status=models.CharField(max_length=32,choices=Visibility.choices,default=Visibility.DRAFT,db_index=True)
    completion_percent=models.PositiveSmallIntegerField(default=0)
    verification_level=models.CharField(max_length=32,choices=VerificationLevel.choices,default=VerificationLevel.NONE,db_index=True)
    verified_at=models.DateTimeField(null=True,blank=True)
    published_at=models.DateTimeField(null=True,blank=True,db_index=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

    class Meta:
        indexes=[
            models.Index(fields=["visibility_status","gender","birth_date"]),
            models.Index(fields=["visibility_status","current_province"]),
            models.Index(fields=["visibility_status","hometown_province"]),
            models.Index(fields=["visibility_status","education_level"]),
            models.Index(fields=["visibility_status","income_band"]),
        ]
    def __str__(self): return self.display_name or self.user.email

class ProfilePhoto(models.Model):
    class Moderation(models.TextChoices): PENDING="pending","Chờ duyệt"; APPROVED="approved","Đã duyệt"; REJECTED="rejected","Từ chối"
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    profile=models.ForeignKey(Profile,on_delete=models.CASCADE,related_name="photos")
    object_key=models.CharField(max_length=500,unique=True)
    public_url=models.URLField(max_length=1000)
    position=models.PositiveSmallIntegerField(default=0)
    is_primary=models.BooleanField(default=False)
    moderation_status=models.CharField(max_length=16,choices=Moderation.choices,default=Moderation.APPROVED)
    width=models.PositiveIntegerField(null=True,blank=True)
    height=models.PositiveIntegerField(null=True,blank=True)
    mime_type=models.CharField(max_length=100)
    file_size=models.PositiveBigIntegerField(default=0)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering=("position","created_at")
        constraints=[models.UniqueConstraint(fields=["profile"],condition=models.Q(is_primary=True),name="unique_primary_photo_per_profile")]

class DiscoveryPreference(models.Model):
    user=models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="discovery_preference")
    min_age=models.PositiveSmallIntegerField(default=18)
    max_age=models.PositiveSmallIntegerField(default=99)
    min_height_cm=models.PositiveSmallIntegerField(null=True,blank=True)
    max_height_cm=models.PositiveSmallIntegerField(null=True,blank=True)
    province_codes=models.JSONField(default=list,blank=True)
    hometown_codes=models.JSONField(default=list,blank=True)
    occupation_ids=models.JSONField(default=list,blank=True)
    education_levels=models.JSONField(default=list,blank=True)
    income_bands=models.JSONField(default=list,blank=True)
    relationship_goals=models.JSONField(default=list,blank=True)
    verified_only=models.BooleanField(default=False)
    updated_at=models.DateTimeField(auto_now=True)
