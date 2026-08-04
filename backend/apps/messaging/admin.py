from django.contrib import admin
from .models import Conversation,ConversationMember,Message
admin.site.register(Conversation);admin.site.register(ConversationMember)
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
 list_display=("conversation","sender","created_at","message_type");search_fields=("sender__email","text");readonly_fields=[f.name for f in Message._meta.fields]
 def has_add_permission(self,request):return False
 def has_change_permission(self,request,obj=None):return False
