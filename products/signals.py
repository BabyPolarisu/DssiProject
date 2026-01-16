from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from allauth.account.signals import user_signed_up
from .models import UserProfile

# 1. เมื่อสมัครผ่าน Social Login (Google)
@receiver(user_signed_up)
def populate_profile(request, user, **kwargs):
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    if user.socialaccount_set.filter(provider='google').exists():
        data = user.socialaccount_set.filter(provider='google')[0].extra_data
        
        # ดึงข้อมูลจาก Google มาใส่เฉพาะตอนที่ข้อมูลยังว่างอยู่
        if not profile.display_name:
            profile.display_name = data.get('name') or user.get_full_name()
        
        # (Optional) ถ้าโมเดลคุณรองรับ avatar_url ก็ดึงรูปมาได้
        # if not profile.avatar:
        #     profile.avatar_url = data.get('picture')
            
        profile.save()

# 2. เมื่อมีการบันทึก User (Save)
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, created, **kwargs):
    # ใช้ get_or_create เพื่อป้องกัน Error (Duplicate Key)
    profile, created_profile = UserProfile.objects.get_or_create(user=instance)

    # Logic: อัปเดตชื่ออัตโนมัติ "เฉพาะตอนสร้างใหม่" หรือ "ถ้าใน Profile ยังว่างเปล่า"
    # ถ้า User เคยแก้ชื่อเองแล้ว เราจะไม่ไปทับมัน
    if created or not profile.display_name:
        full_name = instance.get_full_name().strip()
        if full_name:
            profile.display_name = full_name
            profile.save()