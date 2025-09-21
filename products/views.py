from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login 
from .forms import ProductForm, CustomUserCreationForm 
from .models import Product, Category

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
    return render(request, 'products/product_list.html', {'products': products})

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'products/product_detail.html', {'product': product})

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
            product.save()
            return redirect('product_detail', pk=product.pk)
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