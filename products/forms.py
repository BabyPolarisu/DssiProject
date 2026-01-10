# products/forms.py

from django import forms
from .models import Product, Category, UserProfile, Review
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        # เพิ่ม 'image' เข้าไปใน list นี้
        fields = ['name', 'category', 'price', 'condition', 'description', 'image']
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm',
            }),
            'category': forms.Select(attrs={
                'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'focus:ring-blue-500 focus:border-blue-500 block w-full pl-3 pr-12 sm:text-sm border-gray-300 rounded-md',
            }),
            'condition': forms.RadioSelect(),
            'description': forms.Textarea(attrs={
                'class': 'mt-1 shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border border-gray-300 rounded-md',
                'rows': 4,
            }),
            'image': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'
            })
        }

        labels = {
            'name': 'ชื่อสินค้า *',
            'category': 'หมวดหมู่ *',
            'price': 'ราคา *',
            'condition': 'สภาพสินค้า *',
            'description': 'รายละเอียด',
            'image': 'รูปภาพสินค้า',
        }
        
    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        self.fields['category'].empty_label = "เลือกหมวดหมู่"


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ('email',)

class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        # ✅ เพิ่ม 'display_name' เข้าไปในรายการ fields
        fields = ['display_name', 'phone_number', 'address', 'bio', 'avatar']
        
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
            # เพิ่ม widget ให้ display_name ดูสวยงาม (ถ้าต้องการ)
            'display_name': forms.TextInput(attrs={'class': 'w-full border rounded px-3 py-2', 'placeholder': 'ชื่อที่ใช้แสดงในร้าน'}),
        }

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={'class': 'w-full border rounded-lg px-3 py-2'}),
            'comment': forms.Textarea(attrs={'class': 'w-full border rounded-lg px-3 py-2', 'rows': 3, 'placeholder': 'เขียนรีวิวให้ผู้ขายคนนี้...'}),
        }