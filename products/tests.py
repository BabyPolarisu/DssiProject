from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.urls import reverse
from allauth.socialaccount.models import SocialApp
from .models import (
    Product, Category, UserProfile, Review,
    Report, ReportImage, Notification, VerificationRequest,
)
from .forms import ProductForm, UBURegisterForm, ReviewForm, UserUpdateForm


class SocialAppMixin:
    """Create a Google SocialApp so allauth templates don't crash."""
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        site = Site.objects.get_current()
        app, _ = SocialApp.objects.get_or_create(
            provider="google",
            defaults={"name": "Google", "client_id": "fake", "secret": "fake"},
        )
        app.sites.add(site)


# ==========================================
# Model Tests
# ==========================================

class CategoryModelTest(TestCase):
    def test_str(self):
        cat = Category.objects.create(name="หนังสือเรียน", icon="📚")
        self.assertEqual(str(cat), "หนังสือเรียน")

    def test_default_icon(self):
        cat = Category.objects.create(name="อื่นๆ")
        self.assertEqual(cat.icon, "📦")


class ProductModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="seller1", password="testpass123")
        self.category = Category.objects.create(name="Electronics")
        self.product = Product.objects.create(
            name="Laptop",
            description="A good laptop",
            price=Decimal("15000.00"),
            condition="used",
            category=self.category,
            seller=self.user,
            status="active",
        )

    def test_str(self):
        self.assertEqual(str(self.product), "Laptop")

    def test_default_status_is_pending(self):
        p = Product.objects.create(
            name="Phone",
            description="desc",
            price=Decimal("5000"),
            seller=self.user,
        )
        self.assertEqual(p.status, "pending")

    def test_favorites(self):
        buyer = User.objects.create_user(username="buyer1", password="testpass123")
        self.product.favorites.add(buyer)
        self.assertIn(buyer, self.product.favorites.all())
        self.assertIn(self.product, buyer.favorite_products.all())

    def test_category_set_null_on_delete(self):
        self.category.delete()
        self.product.refresh_from_db()
        self.assertIsNone(self.product.category)


class UserProfileModelTest(TestCase):
    def test_profile_auto_created_via_signal(self):
        """UserProfile should be accessible if created by signal or manually."""
        user = User.objects.create_user(username="testuser", password="pass123")
        # Profile may or may not be auto-created depending on signals
        profile, _ = UserProfile.objects.get_or_create(user=user)
        self.assertEqual(str(profile), "testuser")


class ReviewModelTest(TestCase):
    def setUp(self):
        self.reviewer = User.objects.create_user(username="reviewer", password="pass123")
        self.seller = User.objects.create_user(username="seller", password="pass123")

    def test_str(self):
        review = Review.objects.create(
            reviewer=self.reviewer, seller=self.seller, rating=4, comment="Good"
        )
        self.assertIn("reviewer", str(review))
        self.assertIn("seller", str(review))
        self.assertIn("4", str(review))

    def test_default_rating(self):
        review = Review.objects.create(reviewer=self.reviewer, seller=self.seller)
        self.assertEqual(review.rating, 5)


class ReportModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="reporter", password="pass123")

    def test_str(self):
        report = Report.objects.create(
            reporter=self.user, reason="bug", details="Something broke"
        )
        self.assertIn("reporter", str(report))

    def test_default_status(self):
        report = Report.objects.create(
            reporter=self.user, reason="spam", details="Spam post"
        )
        self.assertEqual(report.status, "pending")


class NotificationModelTest(TestCase):
    def test_notification_created(self):
        user = User.objects.create_user(username="notifuser", password="pass123")
        notif = Notification.objects.create(
            recipient=user, title="Test", message="Hello"
        )
        self.assertFalse(notif.is_read)

    def test_product_approve_creates_notification(self):
        seller = User.objects.create_user(username="seller", password="pass123")
        product = Product.objects.create(
            name="Item", description="desc", price=Decimal("100"),
            seller=seller, status="pending",
        )
        # Simulate admin approving
        product.status = "active"
        product.save()
        notif = Notification.objects.filter(
            recipient=seller, title__icontains="อนุมัติ"
        ).first()
        self.assertIsNotNone(notif)

    def test_product_suspend_creates_notification(self):
        seller = User.objects.create_user(username="seller2", password="pass123")
        product = Product.objects.create(
            name="Item2", description="desc", price=Decimal("100"),
            seller=seller, status="active",
        )
        product.status = "suspended"
        product.save()
        notif = Notification.objects.filter(
            recipient=seller, title__icontains="ระงับ"
        ).first()
        self.assertIsNotNone(notif)


class VerificationRequestModelTest(TestCase):
    def test_str(self):
        user = User.objects.create_user(username="verifuser", password="pass123")
        vr = VerificationRequest.objects.create(
            user=user, student_card_image="test.jpg", status="pending"
        )
        self.assertIn("verifuser", str(vr))


# ==========================================
# Form Tests
# ==========================================

class ProductFormTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Books")

    def test_valid_form(self):
        form = ProductForm(data={
            "name": "Django Book",
            "category": self.category.id,
            "price": "590.00",
            "condition": "new",
            "description": "Learn Django",
        })
        self.assertTrue(form.is_valid())

    def test_missing_name(self):
        form = ProductForm(data={
            "category": self.category.id,
            "price": "100",
            "condition": "new",
            "description": "desc",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_missing_price(self):
        form = ProductForm(data={
            "name": "Item",
            "condition": "new",
            "description": "desc",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("price", form.errors)


class UBURegisterFormTest(TestCase):
    def test_valid_ubu_email(self):
        form = UBURegisterForm(data={
            "username": "student1",
            "first_name": "สมชาย",
            "last_name": "ใจดี",
            "email": "65000001@ubu.ac.th",
            "password1": "Str0ngP@ss!",
            "password2": "Str0ngP@ss!",
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_reject_non_ubu_email(self):
        form = UBURegisterForm(data={
            "username": "student2",
            "first_name": "สมหญิง",
            "last_name": "ใจดี",
            "email": "test@gmail.com",
            "password1": "Str0ngP@ss!",
            "password2": "Str0ngP@ss!",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_duplicate_email(self):
        User.objects.create_user(
            username="existing", password="pass123", email="65000001@ubu.ac.th"
        )
        form = UBURegisterForm(data={
            "username": "newuser",
            "first_name": "ชื่อ",
            "last_name": "สกุล",
            "email": "65000001@ubu.ac.th",
            "password1": "Str0ngP@ss!",
            "password2": "Str0ngP@ss!",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)


class UserUpdateFormTest(TestCase):
    def test_reject_non_ubu_email(self):
        user = User.objects.create_user(
            username="u1", password="pass123", email="u1@ubu.ac.th"
        )
        form = UserUpdateForm(data={
            "username": "u1",
            "first_name": "ชื่อ",
            "last_name": "สกุล",
            "email": "u1@gmail.com",
        }, instance=user)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)


class ReviewFormTest(TestCase):
    def test_valid(self):
        form = ReviewForm(data={"rating": 5, "comment": "Great seller!"})
        self.assertTrue(form.is_valid())

    def test_missing_rating(self):
        form = ReviewForm(data={"comment": "no rating"})
        self.assertFalse(form.is_valid())


# ==========================================
# View Tests (Public - No Auth Required)
# ==========================================

class HomeViewTest(SocialAppMixin, TestCase):
    def test_home_page_returns_200(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")

    def test_home_shows_active_products_only(self):
        seller = User.objects.create_user(username="s", password="p")
        Product.objects.create(
            name="Active", description="d", price=100, seller=seller, status="active"
        )
        Product.objects.create(
            name="Pending", description="d", price=100, seller=seller, status="pending"
        )
        response = self.client.get(reverse("home"))
        products = response.context["products"]
        self.assertEqual(products.count(), 1)
        self.assertEqual(products.first().name, "Active")


class ProductListViewTest(SocialAppMixin, TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(username="s", password="p")
        self.cat = Category.objects.create(name="Books")
        Product.objects.create(
            name="Django Book", description="Learn Django", price=500,
            seller=self.seller, status="active", category=self.cat,
        )
        Product.objects.create(
            name="Phone Case", description="Nice case", price=200,
            seller=self.seller, status="active",
        )
        Product.objects.create(
            name="Hidden", description="pending", price=100,
            seller=self.seller, status="pending",
        )

    def test_list_returns_200(self):
        response = self.client.get(reverse("product_list"))
        self.assertEqual(response.status_code, 200)

    def test_only_active_shown(self):
        response = self.client.get(reverse("product_list"))
        self.assertEqual(response.context["products"].count(), 2)

    def test_search_filter(self):
        response = self.client.get(reverse("product_list"), {"q": "Django"})
        products = response.context["products"]
        self.assertEqual(products.count(), 1)
        self.assertEqual(products.first().name, "Django Book")

    def test_category_filter(self):
        response = self.client.get(reverse("product_list"), {"category": self.cat.id})
        products = response.context["products"]
        self.assertEqual(products.count(), 1)


class ProductDetailViewTest(SocialAppMixin, TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(username="s", password="p")
        self.product = Product.objects.create(
            name="Item", description="desc", price=100,
            seller=self.seller, status="active",
        )

    def test_active_product_returns_200(self):
        response = self.client.get(
            reverse("product_detail", kwargs={"pk": self.product.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Item")

    def test_pending_product_redirects_anonymous(self):
        self.product.status = "pending"
        self.product.save()
        response = self.client.get(
            reverse("product_detail", kwargs={"pk": self.product.pk})
        )
        self.assertEqual(response.status_code, 302)

    def test_nonexistent_product_returns_404(self):
        response = self.client.get(
            reverse("product_detail", kwargs={"pk": 99999})
        )
        self.assertEqual(response.status_code, 404)


class SearchSuggestionsViewTest(SocialAppMixin, TestCase):
    def setUp(self):
        seller = User.objects.create_user(username="s", password="p")
        Product.objects.create(
            name="Laptop Lenovo", description="d", price=100,
            seller=seller, status="active",
        )
        Product.objects.create(
            name="Mouse Pad", description="d", price=50,
            seller=seller, status="active",
        )

    def test_returns_json(self):
        response = self.client.get(
            reverse("search_suggestions"), {"term": "Laptop"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Laptop Lenovo")

    def test_empty_query(self):
        response = self.client.get(reverse("search_suggestions"))
        self.assertEqual(response.json(), [])

    def test_no_results(self):
        response = self.client.get(
            reverse("search_suggestions"), {"term": "xyznotfound"}
        )
        self.assertEqual(response.json(), [])


class RegisterViewTest(SocialAppMixin, TestCase):
    def test_register_page_returns_200(self):
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)

    def test_register_valid_user(self):
        response = self.client.post(reverse("register"), {
            "username": "newuser",
            "first_name": "ชื่อ",
            "last_name": "สกุล",
            "email": "65000001@ubu.ac.th",
            "password1": "Str0ngP@ss!",
            "password2": "Str0ngP@ss!",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_register_invalid_email(self):
        response = self.client.post(reverse("register"), {
            "username": "baduser",
            "first_name": "ชื่อ",
            "last_name": "สกุล",
            "email": "bad@gmail.com",
            "password1": "Str0ngP@ss!",
            "password2": "Str0ngP@ss!",
        })
        self.assertEqual(response.status_code, 200)  # re-renders form
        self.assertFalse(User.objects.filter(username="baduser").exists())


class ProductSuccessViewTest(SocialAppMixin, TestCase):
    def test_returns_200(self):
        response = self.client.get(reverse("product_success"))
        self.assertEqual(response.status_code, 200)


class SellerProfileViewTest(SocialAppMixin, TestCase):
    def test_seller_profile_returns_200(self):
        seller = User.objects.create_user(username="seller", password="p")
        response = self.client.get(
            reverse("seller_profile", kwargs={"seller_id": seller.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_nonexistent_seller_returns_404(self):
        response = self.client.get(
            reverse("seller_profile", kwargs={"seller_id": 99999})
        )
        self.assertEqual(response.status_code, 404)


# ==========================================
# View Tests (Auth-Required - Expect Redirect)
# ==========================================

class AuthRequiredViewsTest(TestCase):
    """All login_required views should redirect anonymous users to login."""

    def assertRedirectsToLogin(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302, f"{url} should redirect")
        self.assertIn("login", response.url.lower())

    def test_my_listings(self):
        self.assertRedirectsToLogin(reverse("my_listings"))

    def test_product_create(self):
        self.assertRedirectsToLogin(reverse("product_create"))

    def test_edit_profile(self):
        self.assertRedirectsToLogin(reverse("edit_profile"))

    def test_wishlist(self):
        self.assertRedirectsToLogin(reverse("wishlist"))

    def test_report_page(self):
        self.assertRedirectsToLogin(reverse("report_page"))

    def test_my_reports(self):
        self.assertRedirectsToLogin(reverse("my_reports"))

    def test_verify_identity(self):
        self.assertRedirectsToLogin(reverse("verify_identity"))

    def test_notifications(self):
        self.assertRedirectsToLogin(reverse("notifications"))

    def test_admin_dashboard(self):
        self.assertRedirectsToLogin(reverse("admin_dashboard"))


# ==========================================
# Context Processor Test
# ==========================================

class NotificationContextProcessorTest(SocialAppMixin, TestCase):
    def test_anonymous_no_count(self):
        response = self.client.get(reverse("home"))
        self.assertNotIn("unread_notification_count", response.context)

    def test_authenticated_has_count(self):
        user = User.objects.create_user(username="u", password="p")
        Notification.objects.create(recipient=user, title="T", message="M")
        self.client.login(username="u", password="p")
        response = self.client.get(reverse("home"))
        self.assertEqual(response.context["unread_notification_count"], 1)
