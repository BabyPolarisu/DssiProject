from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    path('products/', views.product_list_all, name='product_list'),
    path('my-listings/', views.my_listings, name='my_listings'),

    path('product/new/', views.product_create, name='product_create'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('product/<int:pk>/edit/', views.product_update, name='product_update'),
    path('product/<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('product/success/', views.product_success, name='product_success'),
    path('api/search-suggestions/', views.search_suggestions, name='search_suggestions'),
    
]