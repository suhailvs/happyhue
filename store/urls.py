from django.urls import path

from . import views, views_cart, views_checkout, views_product

app_name = "store"

urlpatterns = [
    path("", views.home, name="home"),
    path("shop/<slug:slug>/", views.category, name="category"),
    path("product/<slug:slug>/", views_product.product, name="product"),

    # Cart (JSON)
    path("cart/", views_cart.cart_detail, name="cart"),
    path("cart/add/", views_cart.cart_add, name="cart_add"),
    path("cart/update/", views_cart.cart_update, name="cart_update"),
    path("cart/remove/", views_cart.cart_remove, name="cart_remove"),

    # Checkout and Razorpay
    path("checkout/", views_checkout.checkout, name="checkout"),
    path("checkout/create/", views_checkout.checkout_create, name="checkout_create"),
    path("checkout/verify/", views_checkout.checkout_verify, name="checkout_verify"),
    path("checkout/failed/", views_checkout.checkout_failed, name="checkout_failed"),
    path("order/<str:order_number>/", views_checkout.order_success, name="order_success"),
    path("webhooks/razorpay/", views_checkout.razorpay_webhook, name="razorpay_webhook"),
]
