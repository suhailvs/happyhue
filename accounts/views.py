import json
import logging

from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ImproperlyConfigured
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from .firebase import FirebaseAuthError, verify_phone_token
from .models import User

log = logging.getLogger(__name__)


def _safe_next(request, value):
    """Only follow `next` to this site, never to another host."""
    if value and url_has_allowed_host_and_scheme(value, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return value
    return reverse("store:home")


@ensure_csrf_cookie
def login_page(request):
    nxt = _safe_next(request, request.GET.get("next"))
    if request.user.is_authenticated:
        return redirect(nxt)
    return render(request, "accounts/login.html", {
        "next": nxt,
        "firebase_config": getattr(settings, "FIREBASE_WEB_CONFIG", {}),
    })


def _get_or_create_user(uid, phone):
    """Find the customer by phone (the identity that matters) and attach the Firebase uid."""
    user = User.objects.filter(phone=phone).first() or User.objects.filter(firebase_uid=uid).first()
    if user is None:
        try:
            with transaction.atomic():
                user = User.objects.create_user(phone=phone, firebase_uid=uid)
        except IntegrityError:  # two tabs verifying at once
            user = User.objects.get(phone=phone)
    updates = []
    if user.firebase_uid != uid and not User.objects.exclude(pk=user.pk).filter(firebase_uid=uid).exists():
        user.firebase_uid = uid
        updates.append("firebase_uid")
    if user.phone != phone and not User.objects.exclude(pk=user.pk).filter(phone=phone).exists():
        user.phone = phone  # the customer changed their number in Firebase
        updates.append("phone")
    if updates:
        user.save(update_fields=updates)
    return user


@require_POST
def firebase_login(request):
    try:
        body = json.loads(request.body or b"{}")
    except ValueError:
        body = {}
    try:
        uid, phone = verify_phone_token(body.get("id_token"))
    except FirebaseAuthError as exc:
        return JsonResponse({"ok": False, "message": str(exc)}, status=401)
    except ImproperlyConfigured:
        log.exception("Firebase is not configured")
        return JsonResponse({"ok": False, "message": "Sign-in is not available right now."}, status=500)

    user = _get_or_create_user(uid, phone)
    if not user.is_active:
        return JsonResponse({"ok": False, "message": "This account is disabled."}, status=403)

    # The cart lives in the session, and login() keeps it, so a guest's cart follows them in.
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return JsonResponse({"ok": True, "redirect": _safe_next(request, body.get("next")), "new": not user.name})


@require_POST
def logout_view(request):
    logout(request)
    return redirect("store:home")


@login_required
def my_orders(request):
    orders = request.user.orders.prefetch_related("items")
    return render(request, "accounts/orders.html", {"orders": orders})
