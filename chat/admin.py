from django.contrib import admin
from .models import ChatRoom, Message, Profile # ✅ เพิ่ม Profile

admin.site.register(ChatRoom)
admin.site.register(Message)
admin.site.register(Profile) # ✅ ลงทะเบียน Profile