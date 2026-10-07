"""Run with: python manage.py test accounts

Firebase is mocked at the firebase_admin boundary, so everything after the token check is real."""
import json
import time
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from store.models import Category, Product
from store.models_orders import Order

User = get_user_model()
PHONE = "+919876543210"


def token_claims(**over):
    claims = {
        "uid": "fb-uid-1", "phone_number": PHONE, "auth_time": time.time() - 5,
        "firebase": {"sign_in_provider": "phone"},
    }
    claims.update(over)
    return claims


class FirebaseLoginTests(TestCase):
    def setUp(self):
        patcher = mock.patch("accounts.firebase._app", return_value=object())
        patcher.start()
        self.addCleanup(patcher.stop)

    def login(self, claims=None, **body):
        with mock.patch("accounts.firebase.auth.verify_id_token", return_value=claims or token_claims()) as m:
            res = self.client.post(
                reverse("accounts:firebase_login"), json.dumps({"id_token": "tok", **body}), content_type="application/json"
            )
        return res, m

    def test_new_phone_creates_user_and_signs_in(self):
        res, m = self.login()
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["ok"])
        self.assertTrue(res.json()["new"])
        user = User.objects.get(phone=PHONE)
        self.assertEqual(user.firebase_uid, "fb-uid-1")
        self.assertFalse(user.has_usable_password())
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)
        self.assertEqual(m.call_args.kwargs["clock_skew_seconds"], 10)

    def test_same_phone_logs_into_same_user(self):
        self.login()
        self.client.post(reverse("accounts:logout"))
        res, _ = self.login(token_claims(uid="fb-uid-2"))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().firebase_uid, "fb-uid-2")

    def test_returning_user_with_name_is_not_new(self):
        User.objects.create_user(PHONE, name="Ann")
        res, _ = self.login()
        self.assertFalse(res.json()["new"])

    def test_invalid_token_is_rejected(self):
        from firebase_admin import auth
        with mock.patch("accounts.firebase.auth.verify_id_token", side_effect=auth.InvalidIdTokenError("bad")):
            res = self.client.post(reverse("accounts:firebase_login"), json.dumps({"id_token": "x"}), content_type="application/json")
        self.assertEqual(res.status_code, 401)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(User.objects.count(), 0)

    def test_missing_token_is_rejected(self):
        res = self.client.post(reverse("accounts:firebase_login"), "{}", content_type="application/json")
        self.assertEqual(res.status_code, 401)

    def test_garbage_body_is_rejected(self):
        res = self.client.post(reverse("accounts:firebase_login"), "not json", content_type="application/json")
        self.assertEqual(res.status_code, 401)

    def test_non_phone_provider_is_rejected(self):
        res, _ = self.login(token_claims(firebase={"sign_in_provider": "google.com"}))
        self.assertEqual(res.status_code, 401)
        self.assertEqual(User.objects.count(), 0)

    def test_token_without_phone_is_rejected(self):
        claims = token_claims()
        del claims["phone_number"]
        res, _ = self.login(claims)
        self.assertEqual(res.status_code, 401)

    def test_old_sign_in_is_rejected(self):
        res, _ = self.login(token_claims(auth_time=time.time() - 3600))
        self.assertEqual(res.status_code, 401)
        self.assertEqual(User.objects.count(), 0)

    def test_disabled_user_cannot_sign_in(self):
        User.objects.create_user(PHONE, is_active=False)
        res, _ = self.login()
        self.assertEqual(res.status_code, 403)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_get_not_allowed(self):
        self.assertEqual(self.client.get(reverse("accounts:firebase_login")).status_code, 405)

    def test_next_must_stay_on_this_site(self):
        res, _ = self.login(next="https://evil.example/steal")
        self.assertEqual(res.json()["redirect"], reverse("store:home"))
        self.client.post(reverse("accounts:logout"))
        res, _ = self.login(next="/checkout/")
        self.assertEqual(res.json()["redirect"], "/checkout/")

    def test_guest_cart_survives_login(self):
        cat = Category.objects.create(name="C", slug="c")
        p = Product.objects.create(category=cat, name="Paint", brand="B", price=100, stock=5)
        self.client.post(reverse("store:cart_add"), json.dumps({"product_id": p.pk, "qty": 2}), content_type="application/json")
        self.login()
        self.assertEqual(self.client.get(reverse("store:cart")).json()["count"], 2)

    def test_logout_requires_post_and_signs_out(self):
        self.login()
        self.assertEqual(self.client.get(reverse("accounts:logout")).status_code, 405)
        self.client.post(reverse("accounts:logout"))
        self.assertNotIn("_auth_user_id", self.client.session)


class PagesTests(TestCase):
    def test_login_page_renders_with_firebase_config(self):
        with self.settings(FIREBASE_WEB_CONFIG={"apiKey": "k", "projectId": "p"}):
            res = self.client.get(reverse("accounts:login") + "?next=/checkout/")
        self.assertContains(res, 'id="phoneForm"')
        self.assertContains(res, 'data-next="/checkout/"')
        self.assertContains(res, '"apiKey": "k"')
        self.assertContains(res, "js/login.js")

    def test_login_page_ignores_offsite_next(self):
        res = self.client.get(reverse("accounts:login") + "?next=https://evil.example/")
        self.assertContains(res, 'data-next="/"')      # the form falls back to the home page
        self.assertNotContains(res, "next=https")      # and nothing on the page carries the off-site address

    def test_signed_in_user_is_sent_away_from_login(self):
        self.client.force_login(User.objects.create_user(PHONE))
        res = self.client.get(reverse("accounts:login") + "?next=/checkout/")
        self.assertRedirects(res, "/checkout/", fetch_redirect_response=False)

    def test_orders_page_needs_login(self):
        res = self.client.get(reverse("accounts:orders"))
        self.assertRedirects(res, f'{reverse("accounts:login")}?next={reverse("accounts:orders")}', fetch_redirect_response=False)

    def test_orders_page_lists_only_own_orders(self):
        me, other = User.objects.create_user(PHONE), User.objects.create_user("+919811111111")
        mine, theirs = (make_order(me), make_order(other))
        self.client.force_login(me)
        res = self.client.get(reverse("accounts:orders"))
        self.assertContains(res, mine.order_number)
        self.assertNotContains(res, theirs.order_number)

    def test_header_shows_sign_in_or_account_link(self):
        res = self.client.get(reverse("accounts:login"))
        self.assertContains(res, 'aria-label="Sign in"')
        self.client.force_login(User.objects.create_user(PHONE))
        res = self.client.get(reverse("accounts:orders"))
        self.assertContains(res, 'aria-label="My account and orders"')


def make_order(user, **over):
    fields = dict(
        user=user, full_name="Ann", email="a@b.com", phone="9876543210", address_line1="1 St", city="Kochi",
        state="Kerala", pincode="682001", subtotal=100, total=100,
    )
    fields.update(over)
    return Order.objects.create(**fields)


ADDRESS = {
    "full_name": "Ann Mathew", "email": "ann@example.com", "phone": "9876543210", "address_line1": "1 MG Road",
    "city": "Kochi", "state": "Kerala", "pincode": "682001",
}


class CheckoutAccountTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="C", slug="c")
        self.product = Product.objects.create(category=cat, name="Paint", brand="B", price=500, stock=5)
        self.user = User.objects.create_user(PHONE)

    def add_to_cart(self):
        self.client.post(reverse("store:cart_add"), json.dumps({"product_id": self.product.pk}), content_type="application/json")

    def test_checkout_page_redirects_guests_to_login(self):
        res = self.client.get(reverse("store:checkout"))
        self.assertRedirects(res, f'{reverse("accounts:login")}?next={reverse("store:checkout")}', fetch_redirect_response=False)

    def test_checkout_page_prefills_from_account(self):
        self.user.name, self.user.email = "Ann", "ann@example.com"
        self.user.save()
        self.client.force_login(self.user)
        self.add_to_cart()
        res = self.client.get(reverse("store:checkout"))
        self.assertContains(res, 'value="Ann"')
        self.assertContains(res, 'value="9876543210"')

    def test_guest_cannot_create_an_order(self):
        self.add_to_cart()
        res = self.client.post(reverse("store:checkout_create"), ADDRESS)
        self.assertEqual(res.status_code, 401)
        self.assertIn("login_url", res.json())
        self.assertEqual(Order.objects.count(), 0)

    def test_order_belongs_to_user_and_fills_profile(self):
        self.client.force_login(self.user)
        self.add_to_cart()
        fake_payment = mock.Mock(razorpay_order_id="order_X", amount=0, currency="INR")
        with mock.patch("store.views_checkout.services.create_razorpay_order", return_value=fake_payment):
            res = self.client.post(reverse("store:checkout_create"), ADDRESS)
        self.assertEqual(res.status_code, 200, res.content)
        order = Order.objects.get()
        self.assertEqual(order.user, self.user)
        self.user.refresh_from_db()
        self.assertEqual((self.user.name, self.user.email), ("Ann Mathew", "ann@example.com"))
        self.assertEqual(list(self.user.orders.all()), [order])

    def test_existing_profile_is_not_overwritten(self):
        self.user.name = "Keep Me"
        self.user.save()
        self.client.force_login(self.user)
        self.add_to_cart()
        fake_payment = mock.Mock(razorpay_order_id="order_Y", amount=0, currency="INR")
        with mock.patch("store.views_checkout.services.create_razorpay_order", return_value=fake_payment):
            self.client.post(reverse("store:checkout_create"), ADDRESS)
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, "Keep Me")

    def test_order_page_is_visible_to_owner_only(self):
        order = make_order(self.user)
        url = reverse("store:order_success", args=[order.order_number])
        self.assertEqual(self.client.get(url).status_code, 404)  # guest
        self.client.force_login(User.objects.create_user("+919822222222"))
        self.assertEqual(self.client.get(url).status_code, 404)  # someone else
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(url).status_code, 200)  # owner, even from a new browser


class UserModelTests(TestCase):
    def test_normalize_phone(self):
        from accounts.models import normalize_phone
        for raw, want in [("9876543210", PHONE), ("98765 43210", PHONE), ("+91 98765-43210", PHONE), ("919876543210", PHONE),
                          ("09876543210", ""), ("12345", ""), ("", ""), ("+4420712345678", "+4420712345678")]:
            self.assertEqual(normalize_phone(raw), want, raw)

    def test_create_user_rejects_bad_phone(self):
        with self.assertRaises(ValueError):
            User.objects.create_user("123")

    def test_superuser_needs_password_and_flags(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(PHONE)
        su = User.objects.create_superuser("9876543210", "pw12345!x")
        self.assertTrue(su.is_staff and su.is_superuser)
        self.assertEqual(su.phone, PHONE)
        self.assertEqual(su.national_number, "9876543210")

    def test_staff_can_sign_in_to_admin_with_phone_and_password(self):
        User.objects.create_superuser(PHONE, "pw12345!x")
        self.assertTrue(self.client.login(username=PHONE, password="pw12345!x"))
        self.assertEqual(self.client.get("/admin/").status_code, 200)

    def test_admin_user_pages(self):
        User.objects.create_superuser(PHONE, "pw12345!x")
        self.client.login(username=PHONE, password="pw12345!x")
        customer = User.objects.create_user("+919833333333", name="Bob")
        make_order(customer)
        self.assertContains(self.client.get("/admin/accounts/user/"), "+919833333333")
        self.assertEqual(self.client.get(f"/admin/accounts/user/{customer.pk}/change/").status_code, 200)
        add = self.client.get("/admin/accounts/user/add/")
        self.assertEqual(add.status_code, 200)
        res = self.client.post("/admin/accounts/user/add/", {"phone": "+919844444444", "password1": "pw12345!xyz", "password2": "pw12345!xyz"})
        self.assertEqual(res.status_code, 302, getattr(res, "context", None) and res.context["adminform"].form.errors)
        self.assertTrue(User.objects.filter(phone="+919844444444").exists())
        self.assertEqual(self.client.get("/admin/store/order/").status_code, 200)
