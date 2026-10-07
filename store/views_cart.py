import json

from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .cart import Cart


def _body(request):
    try:
        return json.loads(request.body or b"{}")
    except ValueError:
        return {}


def _int(value, default=1):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@require_GET
@ensure_csrf_cookie
def cart_detail(request):
    return JsonResponse(Cart(request).as_json())


@require_POST
def cart_add(request):
    body = _body(request)
    cart = Cart(request)
    qty = _int(body.get("qty"))
    if body.get("framing"):
        ok = cart.add_framing(body["framing"], qty)
    else:
        ok = cart.add_product(_int(body.get("product_id"), 0), qty)
    data = cart.as_json()
    data["ok"] = ok
    return JsonResponse(data, status=200 if ok else 400)


@require_POST
def cart_update(request):
    body = _body(request)
    cart = Cart(request)
    cart.set_qty(str(body.get("key", "")), _int(body.get("qty"), 0))
    return JsonResponse(cart.as_json())


@require_POST
def cart_remove(request):
    cart = Cart(request)
    cart.remove(str(_body(request).get("key", "")))
    return JsonResponse(cart.as_json())
