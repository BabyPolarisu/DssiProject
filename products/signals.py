from django.db.models.signals import post_save
from django.contrib.auth.models import User
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

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # ถ้าสมัครใหม่ ให้เอาชื่อหน้าอีเมลมาใส่เลย
        display_name = instance.email.split('@')[0] if instance.email else instance.username
        UserProfile.objects.create(user=instance, display_name=display_name)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # ป้องกัน error กรณีไม่มี profile
    if not hasattr(instance, 'userprofile'):
        UserProfile.objects.create(user=instance)
    instance.userprofile.save()

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    # ถ้ามีการสร้าง User ใหม่ (created = True)
    if created:
        # 1. เช็คว่าจะใช้ชื่ออะไร? (มีชื่อจริงไหม? ถ้าไม่มีเอา Username)
        if instance.first_name:
            d_name = f"{instance.first_name} {instance.last_name}".strip()
        else:
            d_name = instance.username

        # 2. สร้าง Profile พร้อมชื่อนั้นทันที
        UserProfile.objects.create(user=instance, display_name=d_name)
    else:
        # ถ้าเป็นการแก้ไข User เก่า ก็ให้เซฟ Profile ตามปกติ
        if hasattr(instance, 'profile'):
            instance.profile.save()