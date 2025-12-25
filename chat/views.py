from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import ChatRoom, Message
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
    room = get_object_or_404(ChatRoom, pk=room_id)
    
    # ป้องกันคนนอกแอบเข้าห้องแชท
    if request.user != room.buyer and request.user != room.seller:
        return redirect('home')

    messages = room.messages.order_by('timestamp')
    
    return render(request, 'chat/room.html', {
        'room': room,
        'messages': messages,
        'current_user': request.user
    })

@login_required
def chat_list(request):
    # ดึงห้องแชททั้งหมดที่ "เรา" มีส่วนเกี่ยวข้อง (ไม่ว่าเป็นคนซื้อ หรือ คนขาย)
    # เรียงตามลำดับเวลาล่าสุด (ต้องแน่ใจว่าใน model ChatRoom มี field created_at)
    rooms = ChatRoom.objects.filter(
        Q(buyer=request.user) | Q(seller=request.user)
    ).order_by('-created_at')

    return render(request, 'chat/list.html', {
        'rooms': rooms
    })