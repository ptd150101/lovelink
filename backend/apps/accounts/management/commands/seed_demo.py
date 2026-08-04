from datetime import date
from django.core.management.base import BaseCommand
from apps.accounts.models import User
from apps.profiles.models import Profile,Province,OccupationCategory,ProfilePhoto
class Command(BaseCommand):
 def handle(self,*args,**kwargs):
  province=Province.objects.first();occupation=OccupationCategory.objects.first()
  if not province or not occupation:raise RuntimeError("Run seed_reference_data first")
  for i,(email,gender,name) in enumerate([("demo.man@lovelink.local",Profile.Gender.MALE,"Minh"),("demo.woman@lovelink.local",Profile.Gender.FEMALE,"Lan")]):
   user,created=User.objects.get_or_create(email=email,defaults={"status":User.Status.ACTIVE,"is_email_verified":True})
   if created:user.set_password("DemoPassword123!");user.save()
   p,_=Profile.objects.get_or_create(user=user,defaults={"birth_date":date(1997+i,1,1)})
   p.display_name=name;p.gender=gender;p.interested_genders=[Profile.Gender.FEMALE if gender==Profile.Gender.MALE else Profile.Gender.MALE];p.current_province=province;p.hometown_province=province;p.height_cm=170-i*8;p.occupation_category=occupation;p.occupation_text="Kỹ sư phần mềm" if i==0 else "Marketing";p.education_level=Profile.Education.UNIVERSITY;p.relationship_status=Profile.RelationshipStatus.SINGLE;p.relationship_goal=Profile.Goal.SERIOUS;p.bio="Tôi là người chân thành, thích đọc sách, du lịch và những cuộc trò chuyện có chiều sâu.";p.looking_for="Tìm người tôn trọng, biết lắng nghe và nghiêm túc trong một mối quan hệ.";p.visibility_status=Profile.Visibility.PUBLISHED;p.completion_percent=90;p.save()
  self.stdout.write(self.style.SUCCESS("Demo users: demo.man@lovelink.local / demo.woman@lovelink.local — password DemoPassword123!"))
