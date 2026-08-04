from django.contrib import admin
from .models import ConnectionRequest
@admin.register(ConnectionRequest)
class ConnectionRequestAdmin(admin.ModelAdmin):
 list_display=("sender","receiver","status","sent_at","expires_at");list_filter=("status",);search_fields=("sender__email","receiver__email")
