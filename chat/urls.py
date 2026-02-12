from django.urls import path
from . import views


urlpatterns = [
    path('start/<int:product_id>/', views.start_chat, name='start_chat'), # ลิงก์จากหน้าสินค้า
    path('room/<int:room_id>/', views.chat_room, name='chat_room'),       # หน้าห้องแชทจริง
    path('room/<int:room_id>/get_new/', views.get_new_messages, name='get_new_messages'),
    
    path('inbox/', views.chat_list, name='chat_list'),  # หน้ารายการแชท

]