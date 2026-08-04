from django.contrib import admin
from .models import *
class PhotoInline(admin.TabularInline): model=ProfilePhoto;extra=0
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
 list_display=("display_name","user","gender","current_province","visibility_status","verification_level","completion_percent")
 list_filter=("visibility_status","verification_level","gender","education_level","income_band")
 search_fields=("display_name","user__email","occupation_text")
 inlines=(PhotoInline,)
admin.site.register(Province);admin.site.register(OccupationCategory);admin.site.register(Interest);admin.site.register(DiscoveryPreference)
