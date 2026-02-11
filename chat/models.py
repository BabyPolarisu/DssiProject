from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from products.models import Product

class ChatRoom(models.Model):
    # --- ส่วนเดิม (ห้ามลบ) ---
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='chat_rooms')
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buyer_chats')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seller_chats')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'buyer')

    def __str__(self):
        return f"Chat: {self.product.name} ({self.buyer} -> {self.seller})"

    # --- ✅ ส่วนที่เพิ่มใหม่ (Helpers สำหรับดึงรูปและชื่อจริง) ---
    
    def get_user_avatar(self, user):
        """ฟังก์ชันช่วยดึงรูปโปรไฟล์ (เช็คจาก Profile หลักก่อน)"""
        try:
            # 1. ลองดึงจาก Profile หลัก (รูปไก่) ในแอป products (ใช้ชื่อฟิลด์ avatar)
            if hasattr(user, 'profile') and user.profile.avatar:
                return user.profile.avatar.url
            
            # 2. ถ้าไม่มี ลองดึงจาก Chat Profile (ใช้ชื่อฟิลด์ image)
            if hasattr(user, 'chat_profile') and user.chat_profile.image:
                return user.chat_profile.image.url
                
        except Exception:
            pass
        return None

    def get_user_display_name(self, user):
        """ฟังก์ชันช่วยดึงชื่อที่ควรแสดง (ชื่อจริง -> ชื่อเล่น -> username)"""
        # 1. ลองดึงชื่อจริง-นามสกุล
        full_name = user.get_full_name()
        if full_name:
            return full_name
            
        # 2. ลองดึง Display Name จาก Profile หลัก
        if hasattr(user, 'profile') and user.profile.display_name:
            return user.profile.display_name
            
        # 3. ถ้าไม่มี ให้ใช้ Username
        return user.username

    # Property สำหรับเรียกใช้ง่ายๆ ใน Template
    @property
    def seller_avatar_url(self):
        return self.get_user_avatar(self.seller)

    @property
    def buyer_avatar_url(self):
        return self.get_user_avatar(self.buyer)

    @property
    def seller_name(self):
        return self.get_user_display_name(self.seller)

    @property
    def buyer_name(self):
        return self.get_user_display_name(self.buyer)
    
    @property
    def queue_sequence(self):
        """คืนค่าลำดับคิวของแชทนี้ (เทียบกับแชทอื่นในสินค้าเดียวกัน)"""
        # นับจำนวนห้องแชทของสินค้านี้ ที่สร้าง "ก่อน" ห้องนี้
        q_count = ChatRoom.objects.filter(
            product=self.product, 
            created_at__lt=self.created_at
        ).count()
        return q_count + 1


class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(blank=True)
    image = models.ImageField(upload_to='chat_images/', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender}: {self.content[:20]}"

    # ✅ เพิ่มส่วนนี้เข้าไปครับ
    @property
    def sender_avatar_url(self):
        # เรียกใช้ฟังก์ชันจาก ChatRoom ที่คุณเขียนไว้แล้ว
        return self.room.get_user_avatar(self.sender)

# --- ส่วนเดิม (Profile ของ Chat - เก็บไว้ตามคำขอ ห้ามลบ) ---
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='chat_profile')
    image = models.ImageField(upload_to='profile_pics/', default='default.jpg', null=True, blank=True)

    def __str__(self):
        return f'{self.user.username} Chat Profile'

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    # ตรวจสอบก่อนว่ามี chat_profile หรือไม่ เพื่อป้องกัน Error
    if hasattr(instance, 'chat_profile'):
        instance.chat_profile.save()