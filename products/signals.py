from django.dispatch import receiver
from allauth.account.signals import user_signed_up
from .models import UserProfile

@receiver(user_signed_up)
def populate_profile(request, user, **kwargs):
    # ตรวจสอบว่ามี Profile หรือยัง ถ้ายังให้สร้าง
    if not hasattr(user, 'userprofile'):
        UserProfile.objects.create(user=user)
    
    # ดึงข้อมูลจาก Google มาใส่ (ถ้าต้องการ)
    if user.socialaccount_set.filter(provider='google').exists():
        data = user.socialaccount_set.filter(provider='google')[0].extra_data
        
        # ตัวอย่าง: ดึงชื่อจริงมาใส่ display_name
        user.userprofile.display_name = data.get('name')
        
        # ตัวอย่าง: ดึงรูปโปรไฟล์ Google มาใส่ avatar (ต้องแก้ model ให้รับ URL หรือโหลดภาพมาเก็บ)
        # user.userprofile.avatar_url = data.get('picture') 
        
        user.userprofile.save()