# products/forms.py

from django import forms
from .models import Product, Category, UserProfile, Review, VerificationRequest
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
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
            'description': 'รายละเอียด *',
            'image': 'รูปภาพสินค้า *',
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

class UserUpdateForm(forms.ModelForm):
    # 1. บังคับให้เป็น required=True (ห้ามว่าง)
    first_name = forms.CharField(
        label="ชื่อจริง",
        required=True, 
        widget=forms.TextInput(attrs={'class': 'form-input w-full rounded-lg border-gray-300', 'placeholder': 'ระบุชื่อจริงภาษาไทย'})
    )
    last_name = forms.CharField(
        label="นามสกุล",
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-input w-full rounded-lg border-gray-300', 'placeholder': 'ระบุบามสกุล'})
    )
    email = forms.EmailField(
        label="อีเมลสถาบัน",
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-input w-full rounded-lg border-gray-300'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'bg-gray-100 text-gray-500 cursor-not-allowed w-full rounded-lg border-gray-300', 'readonly': 'readonly'}),
        }

    # 2. ฟังก์ชันตรวจสอบอีเมล (Validation)
    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        # เปลี่ยน @ubu.ac.th เป็นโดเมนมหาวิทยาลัยของคุณ
        allowed_domain = '@ubu.ac.th' 
        
        if not email.endswith(allowed_domain):
            raise ValidationError(f"กรุณาใช้อีเมลมหาวิทยาลัย ({allowed_domain}) เท่านั้น")
        
        # เช็คว่าอีเมลซ้ำกับคนอื่นไหม (ยกเว้นตัวเอง)
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("อีเมลนี้มีผู้ใช้งานแล้ว")

        return email

# ฟอร์มสำหรับแก้ไขข้อมูลโปรไฟล์เพิ่มเติม (UserProfile)
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['display_name', 'avatar', 'phone_number', 'address', 'bio']
        labels = {
            'display_name': 'ชื่อที่ใช้แสดง / ชื่อร้านค้า',
            'avatar': 'รูปโปรไฟล์',
            'phone_number': 'เบอร์โทรศัพท์',
            'address': 'ที่อยู่จัดส่ง / ติดต่อ',
            'bio': 'เกี่ยวกับฉัน / รายละเอียดร้านค้า',
        }
        widgets = {
            'display_name': forms.TextInput(attrs={'class': 'form-input w-full rounded-lg border-2'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-input w-full rounded-lg border-2'}),
            'address': forms.Textarea(attrs={'class': 'form-textarea w-full rounded-lg border-2', 'rows': 3}),
            'bio': forms.Textarea(attrs={'class': 'form-textarea w-full rounded-lg border-2', 'rows': 4}),
            'avatar': forms.FileInput(attrs={'class': 'file-input w-full border border-2 rounded-lg'}),
        }

class VerificationForm(forms.ModelForm):
    class Meta:
        model = VerificationRequest
        fields = ['student_card_image']
        widgets = {
            'student_card_image': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-red-50 file:text-red-700 hover:file:bg-red-100'
            })
        }

class UBURegisterForm(UserCreationForm):
    first_name = forms.CharField(label="ชื่อจริง", max_length=30, required=True, widget=forms.TextInput(attrs={'placeholder': 'สมชาย'}))
    last_name = forms.CharField(label="นามสกุล", max_length=30, required=True, widget=forms.TextInput(attrs={'placeholder': 'ใจดี'}))
    email = forms.EmailField(label="อีเมลมหาวิทยาลัย (@ubu.ac.th)", required=True, widget=forms.EmailInput(attrs={'placeholder': 'xxxxxxxx@ubu.ac.th'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and not email.endswith('@ubu.ac.th'):
            raise ValidationError("กรุณาใช้อีเมล @ubu.ac.th เท่านั้น")
        if User.objects.filter(email=email).exists():
            raise ValidationError("อีเมลนี้ถูกใช้งานแล้ว")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user