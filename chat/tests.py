from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from products.models import Product
from .models import ChatRoom, Message, Profile


class ChatRoomModelTest(TestCase):
    def setUp(self):
        self.buyer = User.objects.create_user(username="buyer", password="p")
        self.seller = User.objects.create_user(username="seller", password="p")
        self.product = Product.objects.create(
            name="Item", description="d", price=100,
            seller=self.seller, status="active",
        )
        self.room = ChatRoom.objects.create(
            product=self.product, buyer=self.buyer, seller=self.seller,
        )

    def test_str(self):
        self.assertIn("Item", str(self.room))
        self.assertIn("buyer", str(self.room))

    def test_unique_together(self):
        """Same buyer+product should not create duplicate room."""
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            ChatRoom.objects.create(
                product=self.product, buyer=self.buyer, seller=self.seller,
            )

    def test_get_user_avatar_returns_default(self):
        """Chat Profile signal sets default.jpg, so avatar is not None."""
        result = self.room.get_user_avatar(self.buyer)
        self.assertIsNotNone(result)

    def test_get_user_display_name_username(self):
        name = self.room.get_user_display_name(self.buyer)
        self.assertEqual(name, "buyer")

    def test_get_user_display_name_full_name(self):
        self.buyer.first_name = "John"
        self.buyer.last_name = "Doe"
        self.buyer.save()
        name = self.room.get_user_display_name(self.buyer)
        self.assertEqual(name, "John Doe")

    def test_queue_sequence(self):
        self.assertEqual(self.room.queue_sequence, 1)
        buyer2 = User.objects.create_user(username="buyer2", password="p")
        room2 = ChatRoom.objects.create(
            product=self.product, buyer=buyer2, seller=self.seller,
        )
        self.assertEqual(room2.queue_sequence, 2)

    def test_seller_name_property(self):
        self.assertEqual(self.room.seller_name, "seller")

    def test_buyer_name_property(self):
        self.assertEqual(self.room.buyer_name, "buyer")


class MessageModelTest(TestCase):
    def setUp(self):
        self.buyer = User.objects.create_user(username="buyer", password="p")
        self.seller = User.objects.create_user(username="seller", password="p")
        self.product = Product.objects.create(
            name="Item", description="d", price=100,
            seller=self.seller, status="active",
        )
        self.room = ChatRoom.objects.create(
            product=self.product, buyer=self.buyer, seller=self.seller,
        )

    def test_str(self):
        msg = Message.objects.create(
            room=self.room, sender=self.buyer, content="Hello!"
        )
        self.assertIn("buyer", str(msg))
        self.assertIn("Hello!", str(msg))

    def test_ordering(self):
        msg1 = Message.objects.create(room=self.room, sender=self.buyer, content="First")
        msg2 = Message.objects.create(room=self.room, sender=self.seller, content="Second")
        msgs = list(self.room.messages.all())
        self.assertEqual(msgs[0], msg1)
        self.assertEqual(msgs[1], msg2)

    def test_sender_avatar_url_returns_default(self):
        """Chat Profile signal sets default.jpg, so avatar is not None."""
        msg = Message.objects.create(room=self.room, sender=self.buyer, content="Hi")
        self.assertIsNotNone(msg.sender_avatar_url)


class ChatProfileSignalTest(TestCase):
    def test_chat_profile_created_on_user_create(self):
        user = User.objects.create_user(username="newuser", password="p")
        self.assertTrue(hasattr(user, "chat_profile"))
        self.assertIsNotNone(user.chat_profile)


class ChatAuthRequiredViewsTest(TestCase):
    """Chat views should redirect anonymous users to login."""

    def test_chat_list_redirects(self):
        response = self.client.get(reverse("chat_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url.lower())

    def test_chat_room_redirects(self):
        response = self.client.get(reverse("chat_room", kwargs={"room_id": 1}))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url.lower())

    def test_start_chat_redirects(self):
        response = self.client.get(reverse("start_chat", kwargs={"product_id": 1}))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url.lower())
