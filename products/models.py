from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

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