from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"

    def ready(self):
        from django.contrib import admin

        from .admin_forms import StaffMfaAuthenticationForm

        admin.site.login_form = StaffMfaAuthenticationForm
        admin.site.login_template = "admin/login.html"
