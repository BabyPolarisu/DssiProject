"""
ASGI config for unimarket project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unimarket.settings')
django.setup() # สำคัญ: ต้องโหลด Django ก่อน

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import chat.routing  # อ้างอิงไฟล์ routing ของแอป chat

application = ProtocolTypeRouter({
    "http": get_asgi_application(), # ถ้าเปิดเว็บปกติ ให้ใช้ HTTP
    "websocket": AuthMiddlewareStack( # ถ้าเปิด WebSocket (แชท) ให้ผ่านระบบ Login
        URLRouter(
            chat.routing.websocket_urlpatterns # วิ่งไปหา URL ที่เราตั้งไว้ใน chat/routing.py
        )
    ),
})
