"""Order creation and Razorpay helpers. Views stay thin; the money logic lives here."""
import logging

import razorpay
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import Product,Order, OrderItem, Payment

log = logging.getLogger(__name__)


def razorpay_client():
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    client.set_app_details({"title": "Happyhue", "version": "1.0"})
    return client


@transaction.atomic
def create_order_from_cart(cart, cleaned):
    """Snapshot the cart into a pending Order. Returns None if the cart is empty."""
    summary = cart.summary()
    if not summary["lines"]:
        return None
    order = Order.objects.create(
        subtotal=summary["subtotal"], shipping_fee=summary["shipping"], total=summary["total"], **cleaned
    )
    OrderItem.objects.bulk_create([
        OrderItem(
            order=order, product=l["product"], name=l["name"] if l["kind"] == "product" else f'Custom framing, {l["by"]}',
            brand=l["by"] if l["kind"] == "product" else "", unit_price=l["unit_price"],
            quantity=l["qty"], options=l["options"],
        )
        for l in summary["lines"]
    ])
    return order


def create_razorpay_order(order):
    """Create the Razorpay order and our Payment row. Raises on API failure."""
    rp = razorpay_client().order.create({
        "amount": order.total_paise,
        "currency": "INR",
        "receipt": order.order_number,
        "notes": {"order_number": order.order_number},
    })
    return Payment.objects.create(
        order=order, razorpay_order_id=rp["id"], amount=order.total_paise, currency="INR"
    )


@transaction.atomic
def mark_paid(payment_id_local, razorpay_payment_id, signature="", method=""):
    """Idempotent: safe to call from both the browser callback and the webhook."""
    payment = Payment.objects.select_for_update().select_related("order").get(pk=payment_id_local)
    if payment.status == Payment.Status.CAPTURED:
        return False
    payment.status = Payment.Status.CAPTURED
    payment.razorpay_payment_id = razorpay_payment_id
    if signature:
        payment.razorpay_signature = signature
    payment.method = method or payment.method
    payment.error = ""
    payment.save()

    order = Order.objects.select_for_update().get(pk=payment.order_id)
    if order.status in (Order.Status.PENDING, Order.Status.FAILED):
        order.status = Order.Status.PAID
        order.paid_at = timezone.now()
        order.save(update_fields=["status", "paid_at"])
        _decrement_stock(order)
    return True


def _decrement_stock(order):
    for item in order.items.select_related("product"):
        if not item.product_id:
            continue
        product = Product.objects.select_for_update().get(pk=item.product_id)
        if product.stock < item.quantity:
            # Money is already taken; flag it for a human instead of failing the order.
            log.warning("Oversold %s on order %s", product.pk, order.order_number)
            order.notes = (order.notes + f"\nOVERSOLD: {product.name}").strip()
            order.save(update_fields=["notes"])
        product.stock = max(product.stock - item.quantity, 0)
        product.save(update_fields=["stock"])


@transaction.atomic
def mark_failed(payment, reason=""):
    payment = Payment.objects.select_for_update().get(pk=payment.pk)
    if payment.status == Payment.Status.CAPTURED:
        return
    payment.status = Payment.Status.FAILED
    payment.error = reason[:300]
    payment.save(update_fields=["status", "error", "updated_at"])
    # The order stays retryable; a new attempt creates a fresh Payment.
    Order.objects.filter(pk=payment.order_id, status=Order.Status.PENDING).update(status=Order.Status.FAILED)
