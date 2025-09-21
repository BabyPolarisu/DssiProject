from django.contrib import admin, messages
from .models import Product, Category

@admin.action(description="Mark selected products as Active (อนุมัติให้แสดง)")
def make_active(modeladmin, request, queryset):
    queryset.update(status='active')
    messages.success(request, "Selected products have been marked as active.")

@admin.action(description="Mark selected products as Pending (นำกลับไปรออนุมัติ)")
def make_pending(modeladmin, request, queryset):
    queryset.update(status='pending')
    messages.success(request, "Selected products have been marked as pending.")


class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'seller', 'category', 'price', 'status', 'created_at')
    list_filter = ('status', 'condition', 'category')
    search_fields = ('name', 'description', 'seller__username')
    
    actions = [make_active, make_pending]

admin.site.register(Category)
admin.site.register(Product, ProductAdmin)