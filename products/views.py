from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth import login 
from django.contrib import admin
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Avg
from .forms import ProductForm, CustomUserCreationForm, ProfileForm, ReviewForm, UserUpdateForm, ProfileUpdateForm
from django.db.models import Q
from .models import Product, Category, UserProfile, Review
# from .utils import verify_promptpay_qr

def home(request):
    latest_products = Product.objects.filter(status='active').order_by('-created_at')[:8]
    context = {
        'products': latest_products
    }
    return render(request, 'home.html', context)

def product_list_all(request):
    products = Product.objects.filter(status='active').order_by('-created_at')
    categories = Category.objects.all()
    # 1. รับค่าคำค้นหาจากกล่อง Search (name="q")
    query = request.GET.get('q')
    
    # 2. ถ้ามีคำค้นหา ให้กรองสินค้าตาม "ชื่อ" หรือ "คำอธิบาย"
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    selected_category_id = request.GET.get('category')
    if selected_category_id:
        products = products.filter(category_id=selected_category_id)
        
    context = {
        'products': products,
        'categories': categories,
        'selected_category_id': int(selected_category_id) if selected_category_id else None,
        'search_query': query, # (Optional) ส่งค่ากลับไปเผื่ออยากแสดงในช่อง input เดิม
    }
    return render(request, 'products/product_list.html', context)

def product_list(request):
    products = Product.objects.filter(status='active')

    query = request.GET.get('q') 
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query)
        )

    return render(request, 'products/product_list.html', {
        'products': products, 
        'search_query': query
    })

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)

    # Logic: ถ้าสินค้ายังไม่ Active (รออนุมัติ) อนุญาตให้ดูได้เฉพาะ "คนขาย" (เจ้าของ) เท่านั้น
    # คนอื่นกดเข้ามาจะเด้งกลับหน้า Home
    if product.status != 'active' and product.seller != request.user:
        return redirect('home')

    # Logic: สินค้าใกล้เคียง (หมวดเดียวกัน, ไม่ใช่ชิ้นปัจจุบัน, เอามา 4 ชิ้น)
    related_products = Product.objects.filter(
        category=product.category, 
        status='active'
    ).exclude(id=product.id).order_by('?')[:4] 
    # .order_by('?') คือการสุ่มสินค้าขึ้นมาโชว์

    context = {
        'product': product,
        'related_products': related_products
    }
    return render(request, 'products/product_detail.html', context)

def seller_profile(request, seller_id):
    seller = get_object_or_404(User, pk=seller_id)
    products = Product.objects.filter(seller=seller, status='active')
    reviews = Review.objects.filter(seller=seller).order_by('-created_at')

    # ✅ เพิ่มส่วนคำนวณคะแนนเฉลี่ย
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']

    # ถ้าไม่มีรีวิวเลย ให้เป็น 0
    if avg_rating is None:
        avg_rating = 0

    context = {
        'seller': seller,
        'products': products,
        'reviews': reviews,
        'avg_rating': avg_rating, # ✅ ส่งค่าเฉลี่ยไปที่ HTML
        'review_count': reviews.count() # ✅ ส่งจำนวนรีวิวไปด้วย
    }
    return render(request, 'products/seller_profile.html', context)

@login_required
def add_review(request, seller_id):
    seller = get_object_or_404(User, pk=seller_id)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        # บันทึกรีวิว
        Review.objects.create(
            reviewer=request.user,
            seller=seller,
            rating=rating,
            comment=comment
        )
        messages.success(request, 'บันทึกรีวิวเรียบร้อยแล้ว')
        
    return redirect('seller_profile', seller_id=seller_id)

@login_required
def edit_profile(request):
    if request.method == 'POST':
        # ส่งข้อมูลเข้าทั้ง 2 ฟอร์ม
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        # ต้อง Valid ทั้งคู่ถึงจะยอม Save
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'อัปเดตข้อมูลโปรไฟล์เรียบร้อยแล้ว!')
            return redirect('edit_profile') # หรือ redirect ไปหน้า profile_detail
    else:
        # โหลดข้อมูลเดิมมาแสดง
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }
    return render(request, 'products/edit_profile.html', context)

@login_required
def my_listings(request):
    products = Product.objects.filter(seller=request.user).order_by('-created_at')
    context = {
        'products': products
    }
    return render(request, 'products/my_listings.html', context)

@login_required
def product_create(request): 
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = request.user

            product.status = 'pending'             
            product.save()

            return redirect('product_success') 
    else:
        form = ProductForm()
    
    return render(request, 'products/product_form.html', {'form': form})

@login_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if product.seller != request.user:
        return redirect('product_list')

    if request.method == 'POST':

        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('product_detail', pk=product.pk)
    else:
        form = ProductForm(instance=product)

    return render(request, 'products/product_form.html', {'form': form})

@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if product.seller != request.user:
        return redirect('product_list')
        
    if request.method == 'POST':
        product.delete()
        return redirect('product_list')
    return render(request, 'products/product_confirm_delete.html', {'product': product})

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def product_success(request):
    return render(request, 'products/product_success.html')

def search_suggestions(request):
    query = request.GET.get('term', '')
    results = []
    if query:
        products = Product.objects.filter(name__icontains=query, status='active')[:5]
        results = [{'id': p.id, 'name': p.name} for p in products]
    return JsonResponse(results, safe=False)

def is_superuser(user):
    return user.is_superuser

# 1. หน้า Dashboard รวม
@login_required
@user_passes_test(is_superuser) # ล็อคให้เข้าได้แค่แอดมิน
def admin_dashboard(request):
    # ดึงสินค้าที่รออนุมัติ
    pending_products = Product.objects.filter(status='pending').order_by('-created_at')
    active_products = Product.objects.filter(status='active').order_by('-created_at')
    suspended_products = Product.objects.filter(status='suspended').order_by('-updated_at')
    
    # ดึงสถิติต่างๆ
    total_products = Product.objects.count()
    total_users = User.objects.count()
    pending_count = pending_products.count()
    
    context = {
        'pending_products': pending_products,
        'active_products': active_products,
        'total_products': total_products,
        'total_users': total_users,
        'pending_count': pending_count,
        'suspended_products': suspended_products,
    }
    return render(request, 'admin_dashboard.html', context)

# 2. ฟังก์ชันกดอนุมัติสินค้า
@login_required
@user_passes_test(is_superuser)
def approve_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.status = 'active' # เปลี่ยนสถานะเป็นพร้อมขาย
    product.save()
    messages.success(request, f'อนุมัติสินค้า "{product.name}" เรียบร้อยแล้ว')
    return redirect('admin_dashboard')

# 3. ฟังก์ชันกดปฏิเสธ/ลบสินค้า
@login_required
@user_passes_test(is_superuser)
def suspend_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.status = 'suspended' # เปลี่ยนสถานะเป็นระงับ
    product.save()
    messages.warning(request, f'ระงับสินค้า "{product.name}" ชั่วคราวแล้ว')
    return redirect('admin_dashboard')

# เพิ่มฟังก์ชันลบสินค้า (สำหรับแอดมินลบสินค้า Active)
@login_required
@user_passes_test(is_superuser)
def delete_product_admin(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product_name = product.name
    product.delete()
    messages.error(request, f'ลบสินค้า "{product_name}" ออกจากระบบแล้ว')
    return redirect('admin_dashboard')

@login_required
@user_passes_test(is_superuser)
def reject_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    # เก็บชื่อสินค้าไว้แจ้งเตือนก่อนลบ
    product_name = product.name
    # ลบสินค้า
    product.delete()
    messages.error(request, f'ปฏิเสธและลบสินค้า "{product_name}" เรียบร้อยแล้ว')
    return redirect('admin_dashboard')

@login_required
def restore_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.user.is_superuser: # เช็คว่าเป็น Admin
        product.status = 'active'
        product.save()
        messages.success(request, f'คืนสถานะสินค้า "{product.name}" เรียบร้อยแล้ว')
    return redirect('admin_dashboard')

@login_required
def add_review(request, seller_id):
    # ดึงข้อมูลผู้ขาย
    seller_user = get_object_or_404(User, pk=seller_id)
    
    # ป้องกันไม่ให้รีวิวตัวเอง
    if request.user == seller_user:
        messages.error(request, "คุณไม่สามารถรีวิวตัวเองได้")
        return redirect('seller_profile', seller_id=seller_id)

    if request.method == 'POST':
        # ตรวจสอบว่าเคยรีวิวไปหรือยัง?
        # ❌ บรรทัดนี้คือจุดที่น่าจะ Error (reviewed_user -> seller)
        existing_review = Review.objects.filter(reviewer=request.user, seller=seller_user).exists()
        
        if existing_review:
            messages.warning(request, "คุณเคยรีวิวผู้ขายรายนี้ไปแล้ว")
        else:
            rating = request.POST.get('rating')
            comment = request.POST.get('comment')
            
            # บันทึกรีวิว
            Review.objects.create(
                reviewer=request.user,
                seller=seller_user, # ✅ ต้องใช้ seller เท่านั้น (ห้ามใช้ reviewed_user)
                rating=rating,
                comment=comment
            )
            messages.success(request, "บันทึกรีวิวเรียบร้อยแล้ว")
            
    return redirect('seller_profile', seller_id=seller_id)

@login_required
def toggle_favorite(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    
    # เช็คว่าเคยกดถูกใจไปหรือยัง
    if request.user in product.favorites.all():
        # ถ้ามีแล้ว ให้ลบออก (Unfavorite)
        product.favorites.remove(request.user)
        messages.info(request, f'ลบ "{product.name}" ออกจากรายการที่ติดใจแล้ว')
    else:
        # ถ้ายังไม่มี ให้เพิ่มเข้าไป (Favorite)
        product.favorites.add(request.user)
        messages.success(request, f'เพิ่ม "{product.name}" ลงในรายการที่ติดใจแล้ว')
    
    # เด้งกลับไปหน้าเดิมที่กดมา
    return redirect('product_detail', pk=product_id)

@login_required
def wishlist(request):
    # ดึงสินค้าที่ User คนนี้กด favorites เอาไว้
    products = request.user.favorite_products.filter(status='active').order_by('-created_at')
    
    context = {
        'products': products
    }
    return render(request, 'products/wishlist.html', context)

@login_required
def mark_as_sold(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    # 1. เช็คว่าเป็นเจ้าของสินค้าจริงไหม (ห้ามคนอื่นมากดมั่ว)
    if request.user != product.seller:
        messages.error(request, "คุณไม่มีสิทธิ์แก้ไขสินค้านี้")
        return redirect('product_detail', pk=pk)

    # 2. สลับสถานะ (Toggle)
    if product.status == 'active':
        product.status = 'sold'
        messages.success(request, "ปิดการขายเรียบร้อยแล้ว! (Marked as Sold)")
    elif product.status == 'sold':
        product.status = 'active'
        messages.success(request, "เปิดขายสินค้าใหม่อีกครั้ง (Marked as Active)")
    
    product.save()
    return redirect('product_detail', pk=pk)

def seller_profile(request, seller_id): # หรือชื่อ profile_detail ตาม URL ของคุณ
    # 1. ดึงข้อมูลผู้ขาย (ใช้ชื่อตัวแปร seller ให้ตรงกับ HTML)
    seller = get_object_or_404(User, pk=seller_id)
    
    # 2. ดึงสินค้า (ใช้ชื่อ selling_products ให้ตรงกับ HTML)
    # เงื่อนไข: ต้องเป็นของ seller คนนี้ และสถานะต้อง active
    selling_products = Product.objects.filter(seller=seller, status='active').order_by('-created_at')
    
    # 3. ดึงรีวิว
    reviews = Review.objects.filter(seller=seller).order_by('-created_at')
    
    # 4. คำนวณคะแนนเฉลี่ย
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0

    context = {
        'seller': seller,                # ✅ แก้จาก target_user เป็น seller
        'selling_products': selling_products, # ✅ ตรงกับ HTML แล้ว
        'reviews': reviews,
        'review_count': reviews.count(),
        'avg_rating': round(avg_rating, 1),
        'range_5': range(1, 6),
    }
    return render(request, 'products/seller_profile.html', context)