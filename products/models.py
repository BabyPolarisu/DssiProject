from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="ชื่อหมวดหมู่")
    icon = models.CharField(max_length=10, default="📦", verbose_name="ไอคอน/Emoji")

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

# --- โค้ดสำหรับ Choices (เก็บไว้เผื่อใช้กับฟิลด์อื่น) ---
CATEGORY_CHOICES = (
    ('books', '📚 หนังสือเรียน'),
    ('electronics', '💻 อิเล็กทรอนิกส์'),
    ('clothing', '👕 เครื่องแต่งกาย'),
    ('shoes', '👟 รองเท้า'),
    ('accessories', '💍 เครื่องประดับ'),
    ('dorm', '🛋️ ของใช้ในหอ'),
    ('stationary', '📝 อุปกรณ์การเรียน'),
    ('sports', '💪🏻 อุปกรณ์ออกกำลังกาย'),
)

CONDITION_CHOICES = (
    ('new', '✨ มือหนึ่ง (New)'),
    ('used', '📦 มือสอง (Used)'),
)

STATUS_CHOICES = (
    ('pending', 'รอการอนุมัติ'),
    ('active', 'กำลังขาย'),
    ('sold', 'ขายแล้ว'),
    ('rejected', 'ถูกปฏิเสธ'),
)

# ----------------------------------------------------


class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="ชื่อสินค้า")
    image = models.ImageField(upload_to='product_images/', null=True, blank=True, verbose_name="รูปภาพสินค้า")
    description = models.TextField(verbose_name="รายละเอียด")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="ราคา")
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='used', verbose_name="สภาพสินค้า")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="หมวดหมู่")
    seller = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="ผู้ขาย")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', verbose_name="สถานะ")
    favorites = models.ManyToManyField(User, related_name='favorite_products', blank=True, verbose_name="ผู้ที่กดถูกใจ")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    display_name = models.CharField(max_length=100, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="รูปโปรไฟล์")
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.user.username
    
class Review(models.Model):
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_given')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_received')
    rating = models.IntegerField(default=5, choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.reviewer} -> {self.seller} ({self.rating} stars)"
    
class Report(models.Model):
    REPORT_REASONS = [
        ('bug', '🐛 แจ้งปัญหาเว็บไซต์ / บั๊ก'),
        ('fraud', '💸 หลอกลวง / ฉ้อโกง'),
        ('fake', '❌ สินค้าปลอม / ลอกเลียนแบบ'),
        ('harassment', '🤬 คำหยาบคาย / คุกคาม'),
        ('spam', '📢 สแปม / โฆษณา'),
        ('other', '📝 อื่นๆ'),
    ]

    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_sent', verbose_name="ผู้แจ้ง")
    
    # เก็บข้อมูลว่าแจ้งเรื่องอะไร (สินค้า? คน? หรือเว็บ?)
    product = models.ForeignKey('Product', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="สินค้าที่เกี่ยวข้อง")
    reported_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports_received', verbose_name="ผู้ใช้ที่ถูกรายงาน")
    contact_info = models.CharField(max_length=200, blank=True, null=True, verbose_name="ชื่อ/เบอร์ติดต่อกลับ (Optional)")
    
    
    reason = models.CharField(max_length=20, choices=REPORT_REASONS, default='other', verbose_name="หัวข้อปัญหา")
    details = models.TextField(verbose_name="รายละเอียดเพิ่มเติม")

    
    # สถานะเพื่อให้แอดมินจัดการ
    status = models.CharField(max_length=20, choices=[
        ('pending', '⏳ รอตรวจสอบ'),
        ('investigating', '🔍 กำลังตรวจสอบ'),
        ('resolved', '✅ แก้ไขแล้ว'),
        ('ignored', '❌ ปฏิเสธ/ยกเลิก'),
    ], default='pending', verbose_name="สถานะ")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="เวลาที่แจ้ง")

    class Meta:
        verbose_name = "รายงานปัญหา"
        verbose_name_plural = "รายการแจ้งปัญหา (Reports)"
        ordering = ['-created_at']

    def __str__(self):
        return f"Report: {self.get_reason_display()} โดย {self.reporter.username}"

class ReportImage(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='report_evidence/', verbose_name="รูปหลักฐาน")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for Report #{self.report.id}"
    
# ==========================================
# 1. ระบบยืนยันตัวตน (Identity Verification)
# ==========================================
class VerificationRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'รอตรวจสอบ'),
        ('approved', 'อนุมัติแล้ว'),
        ('rejected', 'ปฏิเสธ'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='verification')
    student_card_image = models.ImageField(upload_to='verification_cards/', verbose_name="รูปบัตรนักศึกษา")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_comment = models.TextField(blank=True, null=True, verbose_name="เหตุผล (กรณีปฏิเสธ)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Verifiction: {self.user.username} ({self.status})"

# ==========================================
# 2. ระบบแชท (Chat System)
# ==========================================
class ChatRoom(models.Model):
    # ห้องแชทระหว่างผู้ซื้อและผู้ขาย
    participants = models.ManyToManyField(User, related_name='chat_rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def get_other_user(self, user):
        # ฟังก์ชันหาคู่สนทนา (ไม่ใช่ตัวเรา)
        return self.participants.exclude(id=user.id).first()

class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    image = models.ImageField(upload_to='chat_images/', blank=True, null=True)
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

# ==========================================
# 4. ระบบแจ้งเตือน (Notifications)
# ==========================================
class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True, null=True) # ลิงก์กดแล้วไปไหน
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

# --- Signals สำหรับสร้างแจ้งเตือนอัตโนมัติ ---
@receiver(post_save, sender=Product)
def notify_product_status(sender, instance, created, **kwargs):
    # ถ้าสินค้ามีการแก้ไข (ไม่ใช่สร้างใหม่) และสถานะเปลี่ยน
    if not created:
        if instance.status == 'active':
            Notification.objects.create(
                recipient=instance.seller,
                title="สินค้าได้รับการอนุมัติ ✅",
                message=f"สินค้า '{instance.name}' ของคุณพร้อมขายแล้ว",
                link=f"/product/{instance.id}/"
            )
        elif instance.status == 'suspended':
            Notification.objects.create(
                recipient=instance.seller,
                title="สินค้าถูกระงับ ⚠️",
                message=f"สินค้า '{instance.name}' ถูกระงับ กรุณาติดต่อแอดมิน",
                link=f"/product/{instance.id}/" # หรือลิงก์ไปหน้าแก้ไข
            )