from django.db import models
from django.contrib.auth.models import User
from products.models import Product  # เปลี่ยน products เป็นชื่อแอปที่คุณเก็บ Product ไว้

class ChatRoom(models.Model):
    # ห้องแชทจะผูกกับ "สินค้า" ชิ้นนั้นๆ เสมอ
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='chat_rooms')
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buyer_chats')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seller_chats')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # ป้องกันไม่ให้ผู้ซื้อคนเดิมเปิดห้องแชทซ้ำกับสินค้าเดิม
        unique_together = ('product', 'buyer')

    def __str__(self):
        return f"Chat: {self.product.name} ({self.buyer} -> {self.seller})"

class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender}: {self.content[:20]}"