from datetime import date
from django.contrib.auth import authenticate, password_validation
from rest_framework import serializers
from .models import User, UserPreference

class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=10)
    password_confirm = serializers.CharField(write_only=True)
    birth_date = serializers.DateField(write_only=True)
    accept_terms = serializers.BooleanField(write_only=True)
    def validate_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(email=value).exists(): raise serializers.ValidationError("Không thể đăng ký bằng email này.")
        return value
    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]: raise serializers.ValidationError({"password_confirm": "Mật khẩu không khớp."})
        if not attrs["accept_terms"]: raise serializers.ValidationError({"accept_terms": "Bạn phải đồng ý điều khoản."})
        today=date.today(); born=attrs["birth_date"]
        years=today.year-born.year-((today.month,today.day)<(born.month,born.day))
        if years < 18: raise serializers.ValidationError({"birth_date": "Bạn phải từ 18 tuổi."})
        password_validation.validate_password(attrs["password"])
        return attrs
    def create(self, validated):
        birth_date=validated.pop("birth_date"); validated.pop("password_confirm"); validated.pop("accept_terms")
        user=User.objects.create_user(**validated)
        user.pending_birth_date=birth_date
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    remember = serializers.BooleanField(default=False)
    def validate(self, attrs):
        user=authenticate(self.context["request"], email=attrs["email"].lower(), password=attrs["password"])
        if not user: raise serializers.ValidationError("Email hoặc mật khẩu không chính xác.")
        if user.status not in [User.Status.ACTIVE,User.Status.SCHEDULED_DELETION] or not user.is_active: raise serializers.ValidationError("Tài khoản hiện không thể đăng nhập.")
        attrs["user"]=user; return attrs

class PasswordResetConfirmSerializer(serializers.Serializer):
    token=serializers.CharField(); password=serializers.CharField(min_length=10); password_confirm=serializers.CharField()
    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]: raise serializers.ValidationError({"password_confirm":"Mật khẩu không khớp."})
        password_validation.validate_password(attrs["password"]); return attrs

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields=("id","email","phone","status","is_email_verified","is_phone_verified","created_at")


class UserPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreference
        exclude = ("user",)

class EmailChangeSerializer(serializers.Serializer):
    new_email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate_new_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Không thể sử dụng email này.")
        return value
