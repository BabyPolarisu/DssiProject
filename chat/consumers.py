import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, Message
from django.contrib.auth.models import User

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'

        # เข้ากลุ่มแชท
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # ออกจากกลุ่ม
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # รับข้อความจาก WebSocket (Frontend)
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        sender_id = text_data_json['sender_id']

        # บันทึกลงฐานข้อมูล
        await self.save_message(sender_id, message)

        # ส่งข้อความไปให้ทุกคนในกลุ่ม (รวมถึงตัวเอง)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender_id': sender_id
            }
        )

    # รับข้อความจากกลุ่ม แล้วส่งกลับไปหา Frontend
    async def chat_message(self, event):
        # ส่งต่อข้อมูล JSON ไปให้ Frontend (JavaScript)
        await self.send(text_data=json.dumps(event['message_data']))

    @database_sync_to_async
    def save_message(self, sender_id, message):
        user = User.objects.get(id=sender_id)
        room = ChatRoom.objects.get(id=self.room_id)
        Message.objects.create(sender=user, room=room, content=message)