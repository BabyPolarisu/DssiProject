from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
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

# --- Inlines ---
class ReportImageInline(admin.TabularInline):
    model = ReportImage
    extra = 0
    fields = ['image_preview']
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj and obj.pk and hasattr(obj, 'image') and obj.image:
            try:
                return format_html(
                    '<div style="margin-bottom: 10px;">'
                    '<a href="{0}" target="_blank">'
                    '<img src="{0}" style="max-height: 200px; max-width: 100%; border: 2px solid #ddd; padding: 5px; border-radius: 8px;" />'
                    '</a>'
                    '<p style="color: #666; font-size: 11px; margin-top: 5px;">🔍 คลิกที่รูปเพื่อดูขนาดเต็ม</p>'
                    '</div>',
                    obj.image.url
                )
            except Exception:
                return "ไม่สามารถโหลดรูปภาพได้"
        return "ไม่มีรูปภาพ"
    
    image_preview.short_description = "รูปหลักฐาน"

    def has_add_permission(self, request, obj=None):
        return False

# --- Product Admin ---
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'seller', 'category', 'price', 'status', 'created_at')
    list_filter = ('status', 'condition', 'category')
    search_fields = ('name', 'description', 'seller__username')
    actions = [make_active, make_pending]

# --- Report Admin ---
@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    # แสดงรายละเอียดแบบเต็มในหน้านี้เลยตามคำขอ
    list_display = ('id', 'first_image_preview', 'reason_display', 'full_details_display', 'reporter', 'target_display', 'status_badge', 'created_at')
    list_display_links = ('id', 'first_image_preview', 'reason_display', 'full_details_display')
    
    list_filter = ('status', 'reason', 'created_at')
    search_fields = ('details', 'reporter__username', 'contact_info')
    readonly_fields = ('created_at', 'target_display', 'reporter', 'product', 'reported_user')
    
    inlines = [ReportImageInline]
    list_per_page = 10

    def full_details_display(self, obj):
        """แสดงรายละเอียดการร้องเรียนแบบเต็ม พร้อมจัดฟอร์แมตให้น่าอ่าน"""
        if obj.details:
            return format_html(
                '<div style="max-width: 450px; white-space: normal; line-height: 1.6; '
                'background: #fffbe6; padding: 10px; border-radius: 6px; border: 1px solid #ffe58f; '
                'color: #856404; font-size: 13px;">'
                '{}'
                '</div>',
                obj.details
            )
        return format_html('<i style="color: #ccc;">ไม่มีรายละเอียด</i>')
    full_details_display.short_description = "รายละเอียด (คลิกเพื่อเข้าหน้าจัดการ)"

    def first_image_preview(self, obj):
        """แก้ไข Error: ดึงรูปแรกโดยใช้ Query ตรงจาก ReportImage เพื่อเลี่ยงปัญหา related_name"""
        first_img = ReportImage.objects.filter(report=obj).first()
        if first_img and first_img.image:
            return format_html(
                '<img src="{}" style="width: 60px; height: 60px; object-fit: cover; border-radius: 8px; border: 1px solid #ddd;" />',
                first_img.image.url
            )
        return format_html('<div style="width: 60px; height: 60px; background: #f5f5f5; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #ccc; font-size: 20px;">🖼️</div>')
    first_image_preview.short_description = "รูป"

    def reason_display(self, obj):
        return format_html('<span style="font-weight: 600; color: #1a1a1a;">{}</span>', obj.get_reason_display())
    reason_display.short_description = "หัวข้อ"

    def status_badge(self, obj):
        colors = {'pending': '#faad14', 'investigating': '#1890ff', 'resolved': '#52c41a', 'ignored': '#f5222d'}
        color = colors.get(obj.status, '#bfbfbf')
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 11px; white-space: nowrap;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "สถานะ"

    def target_display(self, obj):
        if obj.product:
            return format_html('<span style="color:#666; font-size:11px;">📦 สินค้า:</span><br><strong>{}</strong>', obj.product.name)
        elif obj.reported_user:
            return format_html('<span style="color:#666; font-size:11px;">👤 ผู้ใช้:</span><br><strong>{}</strong>', obj.reported_user.username)
        return "-"
    target_display.short_description = "เป้าหมาย"

    fieldsets = (
        ('สถานะปัจจุบัน', {'fields': ('status', 'created_at')}),
        ('เนื้อหาการร้องเรียน', {'fields': ('target_display', 'reason', 'details')}),
        ('ข้อมูลผู้แจ้ง', {'fields': ('reporter', 'contact_info')}),
    )

# --- Verification Request Admin ---
@admin.register(VerificationRequest)
class VerificationRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'created_at', 'image_preview')
    list_display_links = ('user', 'image_preview')
    list_filter = ('status',)
    readonly_fields = ('image_preview', 'user', 'created_at')
    actions = ['approve_users', 'reject_users']

    def image_preview(self, obj):
        if obj and obj.student_card_image:
             return format_html('<img src="{0}" style="max-height: 80px; border-radius: 5px; border: 1px solid #ccc;" />', obj.student_card_image.url)
        return "-"
    image_preview.short_description = "รูปบัตร"

    @admin.action(description="อนุมัติผู้ใช้ที่เลือก")
    def approve_users(self, request, queryset):
        queryset.update(status='approved')
        for req in queryset:
            Notification.objects.create(
                recipient=req.user,
                title="ยินดีด้วย! ยืนยันตัวตนสำเร็จ 🎉",
                message="คุณสามารถลงขายสินค้าได้แล้วตอนนี้",
                link="/products/create/"
            )

    @admin.action(description="ปฏิเสธผู้ใช้ที่เลือก")
    def reject_users(self, request, queryset):
        queryset.update(status='rejected')
        for req in queryset:
            Notification.objects.create(
                recipient=req.user,
                title="การยืนยันตัวตนไม่ผ่าน ❌",
                message="กรุณาตรวจสอบเอกสารและส่งใหม่อีกครั้ง",
                link="/verify/"
            )

# --- Register Remaining Models ---
admin.site.register(Category)
admin.site.register(Notification)