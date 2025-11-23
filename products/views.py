from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login 
from django.contrib import admin
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .forms import ProductForm, CustomUserCreationForm, ProfileForm 
from .models import Product, Category, UserProfile
from .utils import verify_promptpay_qr

def home(request):
    latest_products = Product.objects.filter(status='active').order_by('-created_at')[:8]
    context = {
        'products': latest_products
    }
    return render(request, 'home.html', context)

def product_list_all(request):
    products = Product.objects.filter(status='active').order_by('-created_at')
    categories = Category.objects.all()

    selected_category_id = request.GET.get('category')
    if selected_category_id:
        products = products.filter(category_id=selected_category_id)
        
    context = {
        'products': products,
        'categories': categories,
        'selected_category_id': int(selected_category_id) if selected_category_id else None
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

@login_required
def edit_profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        
        if form.is_valid():
            # --- เริ่มส่วนตรวจสอบ QR Code ---
            uploaded_qr = request.FILES.get('promptpay_qr')
            account_num = request.POST.get('account_number')

            # ถ้ามีการอัปโหลด QR ใหม่ และ มีเลขบัญชีมาด้วย
            if uploaded_qr and account_num:
                is_valid, msg = verify_promptpay_qr(uploaded_qr, account_num)
                
                if not is_valid:
                    # ถ้าตรวจสอบไม่ผ่าน ให้แจ้งเตือนและไม่บันทึก
                    messages.error(request, f"เกิดข้อผิดพลาด: {msg}")
                    return render(request, 'edit_profile.html', {'form': form})
            # --- จบส่วนตรวจสอบ ---

            form.save()
            messages.success(request, "บันทึกข้อมูลโปรไฟล์เรียบร้อยแล้ว")
            return redirect('edit_profile') # redirect กลับมาหน้าเดิมเพื่อให้เห็นรูปใหม่
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'edit_profile.html', {'form': form})

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