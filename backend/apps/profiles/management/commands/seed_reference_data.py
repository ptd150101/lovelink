from django.core.management.base import BaseCommand
from apps.profiles.models import Province, OccupationCategory, Interest

PROVINCES = [
    ("01", "Hà Nội"), ("79", "TP. Hồ Chí Minh"), ("48", "Đà Nẵng"),
    ("31", "Hải Phòng"), ("92", "Cần Thơ"), ("27", "Bắc Ninh"),
    ("26", "Vĩnh Phúc"), ("30", "Hải Dương"), ("35", "Ninh Bình"),
    ("36", "Thanh Hóa"), ("38", "Nghệ An"), ("46", "Thừa Thiên Huế"),
    ("56", "Khánh Hòa"), ("60", "Bình Thuận"), ("74", "Bình Dương"),
    ("75", "Đồng Nai"), ("77", "Bà Rịa - Vũng Tàu"), ("89", "An Giang"),
]
OCCUPATIONS = [
    "Công nghệ thông tin", "Kinh doanh", "Tài chính - Ngân hàng", "Giáo dục",
    "Y tế", "Kỹ thuật", "Thiết kế - Sáng tạo", "Luật", "Dịch vụ", "Hành chính - Văn phòng",
    "Nông nghiệp", "Tự do", "Sinh viên", "Khác",
]
INTERESTS = [
    "Du lịch", "Đọc sách", "Phim ảnh", "Âm nhạc", "Thể thao", "Nấu ăn",
    "Cà phê", "Công nghệ", "Nhiếp ảnh", "Thú cưng", "Chạy bộ", "Yoga",
    "Game", "Ngoại ngữ", "Tình nguyện", "Khám phá ẩm thực",
]

class Command(BaseCommand):
    help = "Seed provinces, occupations and interests used by LoveLink onboarding and filters."

    def handle(self, *args, **options):
        for order, (code, name) in enumerate(PROVINCES):
            Province.objects.update_or_create(code=code, defaults={"name": name, "sort_order": order})
        for name in OCCUPATIONS:
            OccupationCategory.objects.get_or_create(name=name)
        for name in INTERESTS:
            Interest.objects.get_or_create(name=name)
        self.stdout.write(self.style.SUCCESS("Reference data seeded."))
