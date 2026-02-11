from django.http import JsonResponse
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import ChatRoom, Message
from .forms import MessageForm
from products.models import Product, Notification

@login_required
def start_chat(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    
    # ป้องกันเจ้าของสินค้าทักหาตัวเอง
    if request.user == product.seller:
        return redirect('product_detail', pk=product_id)

    # ตรวจสอบว่าเคยมีห้องแชทหรือยัง
    chat_room, created = ChatRoom.objects.get_or_create(
        product=product,
        buyer=request.user,
        defaults={'seller': product.seller}
    )
    
    # ส่งต่อไปหน้าแชท (โดยใช้ ID ของห้อง)
    return redirect('chat_room', room_id=chat_room.id)

@login_required
def chat_room(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    
    if request.user != room.buyer and request.user != room.seller:
        return redirect('chat_list')

    if request.method == 'POST':
        content = request.POST.get('content', '')
        image = request.FILES.get('image')

        if content or image:
            # 1. บันทึกลงฐานข้อมูลปกติ
            message = Message.objects.create(
                room=room,
                sender=request.user,
                content=content,
                image=image
            )

            # 2. เตรียมข้อมูลที่จะส่งเข้า WebSocket
            message_data = {
                'sender_id': message.sender.id,
                'content': message.content,
                'image_url': message.image.url if message.image else None,
                'timestamp': message.timestamp.strftime('%H:%M'),
                'sender_avatar': room.get_user_avatar(message.sender) # ใช้ helper ที่คุณมีใน models.py
            }

            # 3. 🔥 ส่งสัญญาณเข้า Channel Layer (Real-time Trigger)
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'chat_{room.id}',  # ชื่อกลุ่มต้องตรงกับใน consumers.py
                {
                    'type': 'chat_message', # ชื่อฟังก์ชันใน consumers.py
                    'message_data': message_data
                }
            )
            
            # ตอบกลับ AJAX (Fallback)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success'})

            return redirect('chat_room', room_id=room.id)

    messages = room.messages.all().order_by('timestamp')
    return render(request, 'chat/room.html', {
        'room': room,
        'messages': messages
    })

@login_required
def chat_list(request):
    # ดึงห้องแชทที่ "เรา" เป็นคนซื้อ (buyer) หรือ เป็นคนขาย (seller)
    rooms = ChatRoom.objects.filter(
        Q(buyer=request.user) | Q(seller=request.user)
    ).order_by('-created_at')  # เรียงจากห้องที่สร้างล่าสุดก่อน
    
    return render(request, 'chat/list.html', {
        'rooms': rooms  # ✅ สำคัญ: ต้องตั้งชื่อ key ว่า 'rooms' ให้ตรงกับ list.html
    })

@login_required
def get_new_messages(request, room_id):
    last_id = request.GET.get('last_id', 0)
    
    new_messages = Message.objects.filter(
        room_id=room_id, 
        id__gt=last_id
    ).order_by('timestamp')
    
    data = []
    for msg in new_messages:
        data.append({
            'id': msg.id,
            'sender_id': msg.sender.id,
            'content': msg.content,
            'image_url': msg.image.url if msg.image else None,
            'timestamp': msg.timestamp.strftime('%H:%M'),
            'sender_avatar': msg.sender_avatar_url # ใช้ Property ที่แก้ไปใน models
        })
        
    return JsonResponse({'messages': data})