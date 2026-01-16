from django.http import JsonResponse
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import ChatRoom, Message
from .forms import MessageForm
from products.models import Product

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
    
    # ตรวจสอบสิทธิ์ (Security Check)
    if request.user != room.buyer and request.user != room.seller:
        return redirect('chat_list')

    if request.method == 'POST':
        content = request.POST.get('content', '')
        image = request.FILES.get('image')

        if content or image:
            message = Message.objects.create(
                room=room,
                sender=request.user,
                content=content,
                image=image
            )
            
            # ✅ อัปเดตล่าสุด: ถ้าเป็น AJAX Request ให้ส่ง JSON กลับไป
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'content': message.content,
                    'image_url': message.image.url if message.image else None,
                    'timestamp': message.timestamp.strftime('%H:%M'), # จัดรูปแบบเวลา
                    'sender_id': message.sender.id
                })

            # (Fallback) ถ้าไม่ใช่ AJAX ให้รีเฟรชหน้าปกติ
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