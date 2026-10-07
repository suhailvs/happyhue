import hmac
import json
import logging

import razorpay
from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from . import services
from .cart import Cart
from .forms import CheckoutForm
from .models import Order, Payment

log = logging.getLogger(__name__)

SESSION_ORDERS = "order_numbers"


def _remember(request, order):
    request.session[SESSION_ORDERS] = [*request.session.get(SESSION_ORDERS, []), order.order_number][-20:]


def checkout(request):
    cart = Cart(request)
    summary = cart.summary()
    if not summary["lines"]:
        return redirect("store:home")
    return render(request, "checkout.html", {
        "form": CheckoutForm(), "summary": summary, "razorpay_key": settings.RAZORPAY_KEY_ID,
    })


@require_POST
def checkout_create(request):
    """Validate the address, snapshot the cart into an Order, create the Razorpay order."""
    form = CheckoutForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"ok": False, "errors": form.errors.get_json_data()}, status=400)

    order = services.create_order_from_cart(Cart(request), form.cleaned_data)
    if order is None:
        return JsonResponse({"ok": False, "message": "Your cart is empty."}, status=400)

    try:
        payment = services.create_razorpay_order(order)
    except Exception:
        log.exception("Razorpay order creation failed for %s", order.order_number)
        order.status = Order.Status.CANCELLED
        order.save(update_fields=["status"])
        return JsonResponse({"ok": False, "message": "We could not start the payment. Please try again."}, status=502)

    _remember(request, order)
    return JsonResponse({
        "ok": True,
        "key": settings.RAZORPAY_KEY_ID,
        "razorpay_order_id": payment.razorpay_order_id,
        "amount": payment.amount,
        "currency": payment.currency,
        "name": "Happyhue",
        "description": f"Order {order.order_number}",
        "prefill": {"name": order.full_name, "email": order.email, "contact": order.phone},
        "order_number": order.order_number,
    })


@require_POST
def checkout_verify(request):
    """Browser callback after the Razorpay modal succeeds. The signature check is what makes it trustworthy."""
    rp_order_id = request.POST.get("razorpay_order_id", "")
    rp_payment_id = request.POST.get("razorpay_payment_id", "")
    signature = request.POST.get("razorpay_signature", "")
    payment = Payment.objects.select_related("order").filter(razorpay_order_id=rp_order_id).first()
    if not payment or payment.order.order_number not in request.session.get(SESSION_ORDERS, []):
        return JsonResponse({"ok": False, "message": "Unknown order."}, status=404)

    try:
        services.razorpay_client().utility.verify_payment_signature({
            "razorpay_order_id": rp_order_id,
            "razorpay_payment_id": rp_payment_id,
            "razorpay_signature": signature,
        })
    except razorpay.errors.SignatureVerificationError:
        services.mark_failed(payment, "Signature verification failed")
        return JsonResponse({"ok": False, "message": "Payment could not be verified."}, status=400)

    services.mark_paid(payment.pk, rp_payment_id, signature)
    Cart(request).clear()
    return JsonResponse({"ok": True, "redirect": reverse("store:order_success", args=[payment.order.order_number])})


@require_POST
def checkout_failed(request):
    """Browser reports payment.failed or a dismissed modal. Informational only; the webhook is the source of truth."""
    payment = Payment.objects.filter(
        razorpay_order_id=request.POST.get("razorpay_order_id", ""),
        order__order_number__in=request.session.get(SESSION_ORDERS, []),
    ).first()
    if payment:
        services.mark_failed(payment, request.POST.get("reason", "Payment failed or cancelled"))
    return JsonResponse({"ok": True})


def order_success(request, order_number):
    # Only the browser session that placed the order can open this page.
    if order_number not in request.session.get(SESSION_ORDERS, []):
        raise Http404
    order = Order.objects.prefetch_related("items").filter(order_number=order_number).first()
    if not order:
        raise Http404
    return render(request, "order_success.html", {"order": order})


@csrf_exempt
@require_POST
def razorpay_webhook(request):
    """Server to server confirmation, covers the case where the customer closes the tab after paying."""
    signature = request.headers.get("X-Razorpay-Signature", "")
    body = request.body.decode("utf-8")
    try:
        services.razorpay_client().utility.verify_webhook_signature(body, signature, settings.RAZORPAY_WEBHOOK_SECRET)
    except razorpay.errors.SignatureVerificationError:
        return HttpResponseBadRequest("bad signature")

    event = json.loads(body)
    entity = event.get("payload", {}).get("payment", {}).get("entity", {})
    payment = Payment.objects.filter(razorpay_order_id=entity.get("order_id", "")).first()
    if not payment:
        return HttpResponse("ok")  # not ours, acknowledge so Razorpay stops retrying

    kind = event.get("event")
    if kind in ("payment.captured", "order.paid"):
        if entity.get("amount") == payment.amount and entity.get("currency") == payment.currency:
            services.mark_paid(payment.pk, entity.get("id", ""), method=entity.get("method", ""))
        else:
            log.error("Webhook amount mismatch for %s", payment.razorpay_order_id)
    elif kind == "payment.failed":
        services.mark_failed(payment, (entity.get("error_description") or "Payment failed"))
    return HttpResponse("ok")
