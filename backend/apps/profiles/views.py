import mimetypes, uuid
from datetime import date
from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics,status
from rest_framework.response import Response
from rest_framework.views import APIView
from common.storage.s3 import head_object,presign_put,delete_object
from apps.audit.services import audit
from apps.moderation.services import blocked_user_ids
from .models import DiscoveryPreference,Interest,OccupationCategory,Profile,ProfilePhoto,Province
from .serializers import *
from .services import profile_completion,publish

ALLOWED_IMAGE_TYPES={"image/jpeg":"jpg","image/png":"png","image/webp":"webp"}

class ReferenceDataView(APIView):
    def get(self,request): return Response({"provinces":ProvinceSerializer(Province.objects.all(),many=True).data,"occupations":OccupationCategorySerializer(OccupationCategory.objects.filter(is_active=True),many=True).data,"interests":InterestSerializer(Interest.objects.filter(is_active=True),many=True).data,"choices":{"genders":Profile.Gender.choices,"education":Profile.Education.choices,"income":Profile.Income.choices,"goals":Profile.Goal.choices,"relationship_status":Profile.RelationshipStatus.choices,"habits":Profile.Habit.choices,"children":Profile.Children.choices,"children_plan":Profile.ChildrenPlan.choices}})

class MyProfileView(APIView):
    def get(self,request): return Response(MyProfileSerializer(request.user.profile).data)
    def patch(self,request):
        profile=request.user.profile; s=ProfileWriteSerializer(profile,data=request.data,partial=True); s.is_valid(raise_exception=True); s.save()
        profile.completion_percent=profile_completion(profile); profile.save(update_fields=["completion_percent","updated_at"])
        audit(actor=request.user,action="profile.updated",target=profile)
        return Response(MyProfileSerializer(profile).data)

class ProfilePublishView(APIView):
    def post(self,request):
        errors=publish(request.user.profile)
        if errors:return Response(errors,status=400)
        audit(actor=request.user,action="profile.published",target=request.user.profile)
        return Response(MyProfileSerializer(request.user.profile).data)

class ProfileHideView(APIView):
    def post(self,request):
        p=request.user.profile;p.visibility_status=Profile.Visibility.HIDDEN_USER;p.save(update_fields=["visibility_status","updated_at"]);audit(actor=request.user,action="profile.hidden",target=p);return Response(MyProfileSerializer(p).data)
    def delete(self,request):
        errors=publish(request.user.profile)
        if errors:return Response(errors,status=400)
        return Response(MyProfileSerializer(request.user.profile).data)

class PhotoPresignView(APIView):
    def post(self,request):
        if request.user.profile.photos.count()>=6:return Response({"detail":"Tối đa 6 ảnh."},status=400)
        content_type=request.data.get("content_type",""); size=int(request.data.get("size",0))
        if content_type not in ALLOWED_IMAGE_TYPES:return Response({"content_type":["Chỉ hỗ trợ JPG, PNG hoặc WebP."]},status=400)
        if size<=0 or size>10*1024*1024:return Response({"size":["Ảnh phải nhỏ hơn 10 MB."]},status=400)
        key=f"profiles/{request.user.pk}/{uuid.uuid4()}.{ALLOWED_IMAGE_TYPES[content_type]}"
        signed=presign_put(settings.S3_PROFILE_BUCKET,key,content_type,is_public=True)
        return Response({"object_key":key,"upload_url":signed.upload_url,"headers":signed.headers,"public_url":signed.public_url,"expires_in":600})

class PhotoCompleteView(APIView):
    def post(self,request):
        key=request.data.get("object_key","")
        if not key.startswith(f"profiles/{request.user.pk}/"):return Response({"detail":"Object key không hợp lệ."},status=400)
        try: meta=head_object(settings.S3_PROFILE_BUCKET,key)
        except Exception:return Response({"detail":"Không tìm thấy ảnh đã upload."},status=400)
        content_type=meta.get("ContentType","");size=meta.get("ContentLength",0)
        if content_type not in ALLOWED_IMAGE_TYPES or size>10*1024*1024:return Response({"detail":"File không hợp lệ."},status=400)
        p=request.user.profile;is_primary=not p.photos.exists();url=f"{settings.S3_PUBLIC_ENDPOINT_URL.rstrip('/')}/{settings.S3_PROFILE_BUCKET}/{key}"
        photo=ProfilePhoto.objects.create(profile=p,object_key=key,public_url=url,position=p.photos.count(),is_primary=is_primary,mime_type=content_type,file_size=size)
        return Response(ProfilePhotoSerializer(photo).data,status=201)

class PhotoReorderView(APIView):
    def patch(self,request):
        ids=request.data.get("photo_ids",[]);photos={str(x.id):x for x in request.user.profile.photos.all()}
        if set(ids)!=set(photos):return Response({"photo_ids":["Danh sách ảnh không hợp lệ."]},status=400)
        for i,pid in enumerate(ids):photos[pid].position=i;photos[pid].save(update_fields=["position"])
        return Response(ProfilePhotoSerializer(request.user.profile.photos.all(),many=True).data)

class PhotoPrimaryView(APIView):
    def post(self,request,pk):
        photo=get_object_or_404(ProfilePhoto,pk=pk,profile=request.user.profile)
        ProfilePhoto.objects.filter(profile=request.user.profile,is_primary=True).update(is_primary=False);photo.is_primary=True;photo.save(update_fields=["is_primary"])
        return Response(ProfilePhotoSerializer(photo).data)

class PhotoDeleteView(APIView):
    def delete(self,request,pk):
        photo=get_object_or_404(ProfilePhoto,pk=pk,profile=request.user.profile)
        if photo.is_primary and request.user.profile.photos.exclude(pk=photo.pk).exists():return Response({"detail":"Hãy chọn ảnh đại diện khác trước."},status=400)
        key=photo.object_key;photo.delete()
        try:delete_object(settings.S3_PROFILE_BUCKET,key)
        except Exception:pass
        return Response(status=204)

class DiscoverView(generics.ListAPIView):
    serializer_class=PublicProfileSerializer
    def get_queryset(self):
        user=self.request.user; q=Profile.objects.filter(visibility_status=Profile.Visibility.PUBLISHED,user__status="active").exclude(user=user)
        blocked=blocked_user_ids(user);q=q.exclude(user_id__in=blocked)
        genders=self.request.query_params.getlist("gender") or user.profile.interested_genders
        if genders:q=q.filter(gender__in=genders)
        min_age=max(18,min(99,int(self.request.query_params.get("min_age",18))));max_age=max(min_age,min(99,int(self.request.query_params.get("max_age",99))));today=date.today()
        def anniversary(year):
            try:return date(year,today.month,today.day)
            except ValueError:return date(year,2,28)
        newest=anniversary(today.year-min_age);oldest=anniversary(today.year-max_age-1)+timezone.timedelta(days=1)
        q=q.filter(birth_date__gte=oldest,birth_date__lte=newest)
        for param,lookup in [("min_height","height_cm__gte"),("max_height","height_cm__lte")]:
            if self.request.query_params.get(param):q=q.filter(**{lookup:int(self.request.query_params[param])})
        multi={"province":"current_province_id__in","hometown":"hometown_province_id__in","occupation":"occupation_category_id__in","education":"education_level__in","income":"income_band__in","goal":"relationship_goal__in"}
        for param,lookup in multi.items():
            vals=self.request.query_params.getlist(param)
            if not vals and self.request.query_params.get(param):vals=self.request.query_params[param].split(",")
            if vals:q=q.filter(**{lookup:vals})
        if self.request.query_params.get("verified") in {"1","true","True"}:q=q.filter(verification_level=Profile.VerificationLevel.IDENTITY)
        sort=self.request.query_params.get("sort","recommended")
        order={"newest":"-published_at","age_asc":"-birth_date","recent":"-user__last_seen_at"}.get(sort,"-verification_level,-completion_percent,-user__last_seen_at")
        return q.select_related("user","current_province","hometown_province","occupation_category").prefetch_related("photos","interests").order_by(*order.split(","))

class PublicProfileDetailView(generics.RetrieveAPIView):
    serializer_class=PublicProfileSerializer;lookup_field="public_id"
    def get_queryset(self):
        return Profile.objects.filter(visibility_status=Profile.Visibility.PUBLISHED,user__status="active").exclude(user_id__in=blocked_user_ids(self.request.user)).select_related("user","current_province","hometown_province","occupation_category").prefetch_related("photos","interests")

class DiscoveryPreferenceView(APIView):
    def get(self,request):
        obj,_=DiscoveryPreference.objects.get_or_create(user=request.user);return Response(DiscoveryPreferenceSerializer(obj).data)
    def put(self,request):
        obj,_=DiscoveryPreference.objects.get_or_create(user=request.user);s=DiscoveryPreferenceSerializer(obj,data=request.data);s.is_valid(raise_exception=True);s.save();return Response(s.data)
