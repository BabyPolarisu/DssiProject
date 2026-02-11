from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth import login 
from django.contrib import admin
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Avg, Q
from .forms import ProductForm, CustomUserCreationForm, ProfileForm, ReviewForm, UBURegisterForm, UserUpdateForm, ProfileUpdateForm, VerificationForm
from .models import Product, Category, UserProfile, Review, Report, ReportImage, VerificationRequest, Notification

# ==========================================
# 🏠 General Views
# ==========================================

def home(request):
    latest_products = Product.objects.filter(status='active').order_by('-created_at')[:8]
    context = {
        'products': latest_products
    }
    return render(request, 'home.html', context)

def product_list_all(request):
    products = Product.objects.filter(status='active').order_by('-created_at')
    categories = Category.objects.all()
    
    # 1. รับค่าคำค้นหา
    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    
    # 2. กรองหมวดหมู่
    selected_category_id = request.GET.get('category')
    if selected_category_id:
        products = products.filter(category_id=selected_category_id)
        
    context = {
        'products': products,
        'categories': categories,
        'selected_category_id': int(selected_category_id) if selected_category_id else None,
        'search_query': query,
    }
    return render(request, 'products/product_list.html', context)

# (ลบ function product_list ที่ซ้ำซ้อนออก ใช้ product_list_all แทน หรือปรับ URL ให้ตรงกัน)

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)

    # ✅ Logic แก้ไข: ให้ Admin ดูสินค้า Pending ได้ด้วย (เพื่อกดอนุมัติ)
    # ถ้าไม่ใช่ Active, ไม่ใช่คนขาย, และ "ไม่ใช่ Admin" -> เด้งกลับ
    if product.status != 'active' and product.seller != request.user and not request.user.is_superuser:
        return redirect('home')

    # สินค้าใกล้เคียง
    related_products = Product.objects.filter(
        category=product.category, 
        status='active'
    ).exclude(id=product.id).order_by('?')[:4] 

    context = {
        'product': product,
        'related_products': related_products
    }
    return render(request, 'products/product_detail.html', context)

def search_suggestions(request):
    query = request.GET.get('term', '')
    results = []
    if query:
        products = Product.objects.filter(name__icontains=query, status='active')[:5]
        results = [{'id': p.id, 'name': p.name} for p in products]
    return JsonResponse(results, safe=False)

def register(request):
    if request.method == 'POST':
        form = UBURegisterForm(request.POST) # เรียกใช้ Form ที่เราสร้าง
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('product_list')
    else:
        form = UBURegisterForm()
    
    return render(request, 'registration/register.html', {'form': form})

# ==========================================
# 🛍️ Product Management (CRUD)
# ==========================================

@login_required
def my_listings(request):
    products = Product.objects.filter(seller=request.user).order_by('-created_at')
    return render(request, 'products/my_listings.html', {'products': products})

@login_required
def product_create(request): 
    # --- ✅ เพิ่ม Logic ตรวจสอบสิทธิ์ตรงนี้ ---
    verification = getattr(request.user, 'verification', None)
    
    if not verification or verification.status != 'approved':
        # ถ้ายังไม่มีข้อมูล หรือ สถานะไม่ใช่ 'approved'
        messages.warning(request, "⚠️ คุณต้องยืนยันตัวตนด้วยบัตรนักศึกษาก่อน จึงจะสามารถลงขายสินค้าได้")
        return redirect('verify_identity') # ดีดไปหน้ายืนยันตัวตนทันที
    # --------------------------------------

    if request.method == 'POST':
        # ... (โค้ดเดิมของคุณ) ...
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

@login_required
def mark_as_sold(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.user != product.seller:
        messages.error(request, "คุณไม่มีสิทธิ์แก้ไขสินค้านี้")
        return redirect('product_detail', pk=pk)

    if product.status == 'active':
        product.status = 'sold'
        messages.success(request, "ปิดการขายเรียบร้อยแล้ว!")
    elif product.status == 'sold':
        product.status = 'active'
        messages.success(request, "เปิดขายสินค้าใหม่อีกครั้ง")
    
    product.save()
    return redirect('product_detail', pk=pk)

def product_success(request):
    return render(request, 'products/product_success.html')

# ==========================================
# 👤 Profile & Reviews
# ==========================================

@login_required
def edit_profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'อัปเดตข้อมูลโปรไฟล์เรียบร้อยแล้ว!')
            return redirect('edit_profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)
    
    # --- แก้ไขตรงนี้ (เปลี่ยน recipient -> seller) ---
    received_reviews = Review.objects.filter(seller=request.user).order_by('-created_at')
    # -------------------------------------------
    
    # คำนวณคะแนนเฉลี่ย
    avg_rating = received_reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    review_count = received_reviews.count()

    context = {
        'u_form': u_form,
        'p_form': p_form,
        'received_reviews': received_reviews,
        'avg_rating': round(avg_rating, 1), 
        'review_count': review_count,
    }

    return render(request, 'products/edit_profile.html', context)

# (ลบ seller_profile อันเก่าออก ใช้ version นี้ที่สมบูรณ์กว่า)
def seller_profile(request, seller_id):
    seller = get_object_or_404(User, pk=seller_id)
    selling_products = Product.objects.filter(seller=seller, status='active').order_by('-created_at')
    reviews = Review.objects.filter(seller=seller).order_by('-created_at')
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0

    context = {
        'seller': seller,
        'selling_products': selling_products,
        'reviews': reviews,
        'review_count': reviews.count(),
        'avg_rating': round(avg_rating, 1),
        'range_5': range(1, 6),
    }
    return render(request, 'products/seller_profile.html', context)

# (ลบ add_review อันเก่าออก ใช้ version นี้ที่มีการเช็คซ้ำ)
@login_required
def add_review(request, seller_id):
    seller_user = get_object_or_404(User, pk=seller_id)
    
    if request.user == seller_user:
        messages.error(request, "คุณไม่สามารถรีวิวตัวเองได้")
        return redirect('seller_profile', seller_id=seller_id)

    if request.method == 'POST':
        # เช็คว่าเคยรีวิวหรือยัง
        existing_review = Review.objects.filter(reviewer=request.user, seller=seller_user).exists()
        
        if existing_review:
            messages.warning(request, "คุณเคยรีวิวผู้ขายรายนี้ไปแล้ว")
        else:
            rating = request.POST.get('rating')
            comment = request.POST.get('comment')
            Review.objects.create(
                reviewer=request.user,
                seller=seller_user,
                rating=rating,
                comment=comment
            )
            messages.success(request, "บันทึกรีวิวเรียบร้อยแล้ว")
            
    return redirect('seller_profile', seller_id=seller_id)

# ==========================================
# ❤️ Favorites / Wishlist
# ==========================================

@login_required
def toggle_favorite(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    if request.user in product.favorites.all():
        product.favorites.remove(request.user)
        messages.info(request, f'ลบ "{product.name}" ออกจากรายการที่ติดใจแล้ว')
    else:
        product.favorites.add(request.user)
        messages.success(request, f'เพิ่ม "{product.name}" ลงในรายการที่ติดใจแล้ว')
    return redirect('product_detail', pk=product_id)

@login_required
def wishlist(request):
    products = request.user.favorite_products.filter(status='active').order_by('-created_at')
    return render(request, 'products/wishlist.html', {'products': products})

# ==========================================
# 🚨 Reports (System with Images)
# ==========================================

@login_required
def report_page(request):
    initial_product_id = request.GET.get('product_id')
    initial_user_id = request.GET.get('user_id')
    
    target_product = None
    target_user = None

    if initial_product_id:
        target_product = get_object_or_404(Product, pk=initial_product_id)
    if initial_user_id:
        target_user = get_object_or_404(User, pk=initial_user_id)

    if request.method == 'POST':
        reason = request.POST.get('reason')
        details = request.POST.get('details')
        # ✅ รับค่า contact_info (จุดที่เคย Error)
        contact_info = request.POST.get('contact_info')
        # ✅ รับค่ารูปภาพ
        images = request.FILES.getlist('evidence_images')

        # Backend Validation
        if len(images) > 6:
            messages.error(request, "คุณสามารถแนบรูปได้สูงสุด 6 รูปเท่านั้น")
            return redirect(request.path)
        
        # 1. สร้าง Report
        report = Report.objects.create(
            reporter=request.user,
            reason=reason,
            details=details,
            contact_info=contact_info, # บันทึกลง DB
            product=target_product,
            reported_user=target_user 
        )

        # 2. บันทึกรูปภาพ
        if images:
            for img in images:
                ReportImage.objects.create(report=report, image=img)
                print(f"Saved image: {img.name}")
        
        messages.success(request, "ขอบคุณสำหรับการแจ้งปัญหา เราจะตรวจสอบโดยเร็วที่สุด")
        return redirect('my_reports')

    context = {
        'target_product': target_product,
        'target_user': target_user,
    }
    return render(request, 'products/report.html', context)

@login_required
def my_reports(request):
    reports = Report.objects.filter(reporter=request.user).order_by('-created_at')
    context = {
        'reports': reports,
        'report_count': reports.count()
    }
    return render(request, 'products/my_reports.html', context)

# ==========================================
# 🛠️ Admin Dashboard
# ==========================================

def is_superuser(user):
    return user.is_superuser

@login_required
@user_passes_test(is_superuser)
def admin_dashboard(request):
    pending_products = Product.objects.filter(status='pending').order_by('-created_at')
    active_products = Product.objects.filter(status='active').order_by('-created_at')
    suspended_products = Product.objects.filter(status='suspended').order_by('-updated_at')
    
    context = {
        'pending_products': pending_products,
        'active_products': active_products,
        'suspended_products': suspended_products,
        'total_products': Product.objects.count(),
        'total_users': User.objects.count(),
        'pending_count': pending_products.count(),
    }
    return render(request, 'admin_dashboard.html', context)

@login_required
@user_passes_test(is_superuser)
def approve_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.status = 'active'
    product.save()
    messages.success(request, f'อนุมัติสินค้า "{product.name}" เรียบร้อยแล้ว')
    return redirect('admin_dashboard')

@login_required
@user_passes_test(is_superuser)
def suspend_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.status = 'suspended'
    product.save()
    messages.warning(request, f'ระงับสินค้า "{product.name}" ชั่วคราวแล้ว')
    return redirect('admin_dashboard')

@login_required
@user_passes_test(is_superuser)
def delete_product_admin(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    messages.error(request, f'ลบสินค้าออกจากระบบแล้ว')
    return redirect('admin_dashboard')

@login_required
@user_passes_test(is_superuser)
def reject_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    messages.error(request, f'ปฏิเสธและลบสินค้าเรียบร้อยแล้ว')
    return redirect('admin_dashboard')

@login_required
def restore_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.user.is_superuser:
        product.status = 'active'
        product.save()
        messages.success(request, f'คืนสถานะสินค้าเรียบร้อยแล้ว')
    return redirect('admin_dashboard')

@login_required
def verify_identity(request):
    # เช็คสถานะปัจจุบัน
    existing_req = getattr(request.user, 'verification', None)
    
    if request.method == 'POST':
        form = VerificationForm(request.POST, request.FILES)
        if form.is_valid():
            if existing_req:
                # กรณีเคยส่งแล้ว (เช่น แก้ไขรูปใหม่)
                existing_req.student_card_image = form.cleaned_data['student_card_image']
                existing_req.status = 'pending' # เปลี่ยนสถานะกลับเป็นรอตรวจ
                existing_req.save()
            else:
                # กรณีส่งครั้งแรก
                vr = form.save(commit=False)
                vr.user = request.user
                vr.save()
            
            messages.success(request, 'ส่งเอกสารยืนยันตัวตนแล้ว กรุณารอแอดมินตรวจสอบ')
            return redirect('verify_identity')
    else:
        form = VerificationForm()

    return render(request, 'products/verify_identity.html', {
        'form': form,
        'existing_req': existing_req
    })

# --- 2. ระบบแชท (แบบ Real-time Polling) ---
@login_required
def start_chat(request, seller_id):
    other_user = get_object_or_404(User, pk=seller_id)
    if request.user == other_user:
        return redirect('home')

    # หาห้องแชทที่มีแค่เรากับเขา
    room = ChatRoom.objects.filter(participants=request.user).filter(participants=other_user).first()
    if not room:
        room = ChatRoom.objects.create()
        room.participants.add(request.user, other_user)
    
    return redirect('chat_room', room_id=room.id)

@login_required
def chat_room(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id, participants=request.user)
    other_user = room.get_other_user(request.user)
    
    # ถ้ามีการส่งข้อความ
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Message.objects.create(room=room, sender=request.user, content=content)
            # แจ้งเตือนอีกฝ่าย
            Notification.objects.create(
                recipient=other_user,
                title=f"ข้อความใหม่จาก {request.user.username}",
                message=content[:30],
                link=f"/chat/{room.id}/"
            )
            return redirect('chat_room', room_id=room.id)

    messages_list = room.messages.all().order_by('timestamp')
    return render(request, 'products/chat_room.html', {
        'room': room,
        'other_user': other_user,
        'messages': messages_list
    })

# --- 3. ระบบแจ้งเตือน ---
@login_required
def notifications_view(request):
    # ดึงแจ้งเตือนทั้งหมดของฉัน (ใหม่สุดขึ้นก่อน)
    notifs = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    
    # เมื่อกดเข้ามาหน้านี้ ถือว่า "อ่านแล้ว" ทั้งหมด (ล้างเลขแจ้งเตือน)
    notifs.filter(is_read=False).update(is_read=True)
    
    return render(request, 'products/notifications.html', {'notifications': notifs})