from django.contrib import admin
from .models import CallSession
@admin.register(CallSession)
class CallSessionAdmin(admin.ModelAdmin):list_display=("caller","callee","status","created_at","connected_at","ended_at");list_filter=("status",);search_fields=("caller__email","callee__email","room_name")
