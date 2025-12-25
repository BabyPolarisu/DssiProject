from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    path('products/', views.product_list_all, name='product_list'),
    path('my-listings/', views.my_listings, name='my_listings'),
    path('accounts/', include('allauth.urls')),

    path('product/new/', views.product_create, name='product_create'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('product/<int:pk>/edit/', views.product_update, name='product_update'),
    path('product/<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('product/success/', views.product_success, name='product_success'),
    path('api/search-suggestions/', views.search_suggestions, name='search_suggestions'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/admin/approve/<int:pk>/', views.approve_product, name='approve_product'),
    path('dashboard/admin/reject/<int:pk>/', views.reject_product, name='reject_product'),
    path('dashboard/admin/suspend/<int:pk>/', views.suspend_product, name='suspend_product'),
    path('dashboard/admin/delete/<int:pk>/', views.delete_product_admin, name='delete_product_admin'),
    path('product/restore/<int:pk>/', views.restore_product, name='restore_product'),
    
    
]