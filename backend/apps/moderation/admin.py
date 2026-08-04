from django.contrib import admin
from .models import Block,Report,ModerationAction
admin.site.register(Block)
@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):list_display=("reported_user","reason_code","target_type","status","created_at");list_filter=("status","reason_code","target_type");search_fields=("reported_user__email","reporter__email","description")
admin.site.register(ModerationAction)
