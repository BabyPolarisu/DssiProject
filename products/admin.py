from django.contrib import admin
from django.contrib import messages # ✅ ต้อง Import อันนี้ด้วย ไม่งั้น Action Functions จะ Error
from django.utils.html import format_html
# ✅ ลบ ReportAdmin ออกจากบรรทัดนี้ เพราะเราประกาศ Class ในไฟล์นี้เอง
from .models import Product, Category, Report, ReportImage, VerificationRequest, Notification

# --- Action Functions ---
@admin.action(description="Mark selected products as Active (อนุมัติให้แสดง)")
def make_active(modeladmin, request, queryset):
    queryset.update(status='active')
    messages.success(request, "Selected products have been marked as active.")

@admin.action(description="Mark selected products as Pending (นำกลับไปรออนุมัติ)")
def make_pending(modeladmin, request, queryset):
    queryset.update(status='pending')
    messages.success(request, "Selected products have been marked as pending.")

# --- Inlines (ต้องประกาศก่อน Admin Class ที่จะเรียกใช้) ---
class ReportImageInline(admin.TabularInline):
    model = ReportImage
    extra = 0
    # ✅ เพิ่มบรรทัดนี้: บังคับให้โชว์แค่รูปตัวอย่าง (ซ่อนชื่อไฟล์ที่เป็น Text)
    fields = ['image_preview'] 
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.image:
            # เพิ่ม <a> เพื่อให้คลิกแล้วเปิดดูรูปใหญ่ tab ใหม่ได้
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" style="max-height: 150px; border-radius: 8px;" /></a>', 
                obj.image.url, 
                obj.image.url
            )
        return "-"
    image_preview.short_description = "หลักฐานรูปภาพ"

# --- Product Admin ---
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'seller', 'category', 'price', 'status', 'created_at')
    list_filter = ('status', 'condition', 'category')
    search_fields = ('name', 'description', 'seller__username')
    actions = [make_active, make_pending]

# --- Report Admin ---
@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'reason_badge', 'reporter', 'target_display', 'status_badge', 'created_at')
    list_filter = ('status', 'reason', 'created_at')
    search_fields = ('details', 'reporter__username', 'contact_info')
    readonly_fields = ('created_at',)
    
    # ✅ เรียกใช้ Inline ได้แล้ว เพราะประกาศไว้ข้างบน
    inlines = [ReportImageInline] 
    list_per_page = 20

    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'investigating': 'blue',
            'resolved': 'green',
            'ignored': 'red',
        }
        color = colors.get(obj.status, 'gray')
        label = obj.get_status_display()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 10px; font-weight: bold;">{}</span>',
            color, label
        )
    status_badge.short_description = "สถานะ"

    def reason_badge(self, obj):
        return format_html(
            '<strong>{}</strong>', obj.get_reason_display()
        )
    reason_badge.short_description = "หัวข้อปัญหา"

    def target_display(self, obj):
        if obj.product:
            return format_html('📦 สินค้า: <a href="/admin/products/product/{}/change/">{}</a>', obj.product.id, obj.product.name)
        elif obj.reported_user:
            return format_html('👤 ผู้ใช้: {}', obj.reported_user.username)
        return "-"
    target_display.short_description = "ร้องเรียนเกี่ยวกับ"

@admin.register(VerificationRequest)
class VerificationRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'created_at', 'image_preview')
    list_filter = ('status',)
    readonly_fields = ('image_preview',)
    actions = ['approve_users', 'reject_users']

    def image_preview(self, obj):
        if obj.student_card_image:
             return format_html('<a href="{}" target="_blank"><img src="{}" style="max-height: 100px;" /></a>', obj.student_card_image.url, obj.student_card_image.url)
        return "-"

    @admin.action(description="อนุมัติผู้ใช้ที่เลือก")
    def approve_users(self, request, queryset):
        queryset.update(status='approved')
        # ✅ Loop สร้างแจ้งเตือน
        for req in queryset:
            Notification.objects.create(
                recipient=req.user,
                title="ยินดีด้วย! ยืนยันตัวตนสำเร็จ 🎉",
                message="คุณสามารถลงขายสินค้าได้แล้วตอนนี้",
                link="/products/create/" # ลิงก์ไปหน้าขายของ
            )

    @admin.action(description="ปฏิเสธผู้ใช้ที่เลือก")
    def reject_users(self, request, queryset):
        queryset.update(status='rejected')
        # ✅ Loop สร้างแจ้งเตือน
        for req in queryset:
            Notification.objects.create(
                recipient=req.user,
                title="การยืนยันตัวตนไม่ผ่าน ❌",
                message="กรุณาตรวจสอบเอกสารและส่งใหม่อีกครั้ง",
                link="/verify/" # ลิงก์ไปหน้าแก้ตัว
            )

# --- Register Models ---
admin.site.register(Category)
admin.site.register(Product, ProductAdmin)
