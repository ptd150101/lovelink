from django.contrib import admin
from .models import VerificationRequest,VerificationEvidence,VerificationReview
class EvidenceInline(admin.TabularInline):model=VerificationEvidence;extra=0;readonly_fields=("private_object_key","mime_type","file_size","uploaded_at","deleted_at")
class ReviewInline(admin.TabularInline):model=VerificationReview;extra=0;readonly_fields=[f.name for f in VerificationReview._meta.fields]
@admin.register(VerificationRequest)
class VerificationRequestAdmin(admin.ModelAdmin):list_display=("user","status","submitted_at","assigned_reviewer","decided_at");list_filter=("status",);search_fields=("user__email","user__profile__display_name");inlines=(EvidenceInline,ReviewInline)
