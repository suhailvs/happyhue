# Cart + Razorpay checkout: wiring steps

## 1. Install
    pip install razorpay

## 2. Files (copy into your project)
| File | Destination |
|---|---|
| models_orders.py, cart.py, forms.py, services.py, views_cart.py, views_checkout.py, admin_orders.py | store/ |
| urls.py | store/ (replaces yours) |
| checkout.html, order_success.html | templates/ |
| cart.js, checkout.js | static/js/ |

## 3. Hook up models and admin
Bottom of store/models.py:

    from .models_orders import Order, OrderItem, Payment  # noqa: E402,F401

store/admin.py:

    from .admin_orders import *  # noqa

Then:

    python manage.py makemigrations store && python manage.py migrate

## 4. settings.py
    RAZORPAY_KEY_ID = os.environ["RAZORPAY_KEY_ID"]
    RAZORPAY_KEY_SECRET = os.environ["RAZORPAY_KEY_SECRET"]
    RAZORPAY_WEBHOOK_SECRET = os.environ["RAZORPAY_WEBHOOK_SECRET"]
    SHIPPING_FEE = 99   # charged under the free shipping threshold
    # sessions must be enabled (default). Use test keys (rzp_test_...) first.

## 5. Templates
- base.html: add `<script src="{% static 'js/cart.js' %}"></script>` after site.js, and
  remove the cart logic from site.js (keep wishlist). Change the drawer's Checkout
  button text if you like; cart.js already points it to /checkout/.
- category.html: the first line of the copy you sent starts with a stray `+`
  (`+{% extends ...`). Delete it or the page renders a "+" above the content.

## 6. Frame builder
In static/js/home.js, make the "Add framing to cart" button call:

    window.HHCart.addFraming({size, frame, mat, width, glazing})

using the currently selected keys. The server recomputes the price, so the
browser price is display only.

## 7. Razorpay dashboard
Webhook URL: https://YOUR-DOMAIN/webhooks/razorpay/
Events: payment.captured, order.paid, payment.failed. Use the same secret as
RAZORPAY_WEBHOOK_SECRET. For local testing use a tunnel (ngrok).

## How it works
1. Cart lives in the session; prices are always read from the DB / FRAME_BUILDER.
2. POST /checkout/create/ validates the address, snapshots the cart into
   Order + OrderItems (pending), creates a Razorpay order and a Payment row.
3. Razorpay modal opens. On success the browser posts the signature to
   /checkout/verify/, which verifies it, marks the order paid, decrements stock
   and clears the cart.
4. The webhook does the same idempotently, so paid orders are never lost if the
   customer closes the tab.
