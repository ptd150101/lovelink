import pytest
from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.profiles.models import Profile,Province,OccupationCategory

@pytest.fixture
def api_client():return APIClient()

@pytest.fixture
def province(db):return Province.objects.create(code="01",name="Hà Nội")

@pytest.fixture
def occupation(db):return OccupationCategory.objects.create(name="Công nghệ thông tin")

@pytest.fixture
def user_factory(db,province,occupation):
 def make(email="user@example.com",**kwargs):
  user=User.objects.create_user(email=email,password="StrongPassword123!",status=User.Status.ACTIVE,is_email_verified=True)
  profile=Profile.objects.create(user=user,birth_date=kwargs.pop("birth_date",__import__("datetime").date(1998,1,1)),display_name=kwargs.pop("display_name",email.split("@")[0]),gender=kwargs.pop("gender",Profile.Gender.FEMALE),interested_genders=kwargs.pop("interested_genders",[Profile.Gender.MALE]),current_province=province,hometown_province=province,height_cm=kwargs.pop("height_cm",165),occupation_category=occupation,occupation_text="Kỹ sư",education_level=Profile.Education.UNIVERSITY,relationship_status=Profile.RelationshipStatus.SINGLE,relationship_goal=Profile.Goal.SERIOUS,bio="Tôi là một người chân thành, thích đọc sách, du lịch và mong muốn tìm hiểu nghiêm túc.",looking_for="Một người tôn trọng, biết lắng nghe và có mục tiêu rõ ràng.",**kwargs)
  return user
 return make
