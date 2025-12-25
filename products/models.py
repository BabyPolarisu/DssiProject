from django.db import models
from django.contrib.auth.models import User

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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    display_name = models.CharField(max_length=100, verbose_name="ชื่อที่แสดง")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="รูปโปรไฟล์")
    
    # ข้อมูลการชำระเงิน
    promptpay_qr = models.ImageField(upload_to='payment_qr/', blank=True, null=True, verbose_name="QR Code PromptPay")
    bank_name = models.CharField(max_length=100, blank=True, verbose_name="ธนาคาร")
    account_number = models.CharField(max_length=20, blank=True, verbose_name="เลขที่บัญชี")
    account_name = models.CharField(max_length=100, blank=True, verbose_name="ชื่อบัญชี")

    def __str__(self):
        return self.user.username
    
