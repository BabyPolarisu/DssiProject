# products/models.py

from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="ชื่อหมวดหมู่")
    
    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

# --- โค้ดสำหรับ Choices (เก็บไว้เผื่อใช้กับฟิลด์อื่น) ---
CONDITION_CHOICES = (
    ('new', 'ของใหม่'),
    ('used', 'มือสอง'),
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
    category = models.ForeignKey(Category, on_delete=models.SET_NULL,null=True, blank=True, verbose_name="หมวดหมู่") 
    seller = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="ผู้ขาย")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', verbose_name="สถานะ")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name