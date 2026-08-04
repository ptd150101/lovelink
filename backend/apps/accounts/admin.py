from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User,UserSession
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering=("email",); list_display=("email","status","is_email_verified","is_staff","created_at")
    fieldsets=((None,{"fields":("email","password")}), ("Status",{"fields":("status","is_active","is_email_verified","is_phone_verified","scheduled_deletion_at")}), ("Permissions",{"fields":("is_staff","is_superuser","groups","user_permissions")}), ("Dates",{"fields":("last_login","last_seen_at","date_joined","created_at","updated_at")}))
    readonly_fields=("created_at","updated_at")
    add_fieldsets=((None,{"classes":("wide",),"fields":("email","password1","password2","is_staff","is_superuser")}),)
admin.site.register(UserSession)
