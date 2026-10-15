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

from .google_signin import GoogleAuthFailed, verify_google_token
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
        "google_client_id": getattr(settings, "GOOGLE_CLIENT_ID", ""),
    })


def _get_or_create_user(sub, email, name):
    """Find the customer by Google id, then by email, and attach the Google id. Returns (user, created)."""
    created = False
    user = User.objects.filter(google_sub=sub).first() or User.objects.filter(email__iexact=email).first()
    if user is None:
        try:
            with transaction.atomic():
                user = User.objects.create_user(email=email, google_sub=sub, name=name)
                created = True
        except IntegrityError:  # two tabs verifying at once
            user = User.objects.get(email__iexact=email)
    updates = []
    if not user.google_sub:
        user.google_sub = sub
        updates.append("google_sub")
    if name and not user.name:
        user.name = name
        updates.append("name")
    if updates:
        user.save(update_fields=updates)
    return user, created


@require_POST
def google_login(request):
    try:
        body = json.loads(request.body or b"{}")
    except ValueError:
        body = {}
    try:
        sub, email, name = verify_google_token(body.get("credential"))
    except GoogleAuthFailed as exc:
        return JsonResponse({"ok": False, "message": str(exc)}, status=401)
    except ImproperlyConfigured:
        log.exception("Google sign-in is not configured")
        return JsonResponse({"ok": False, "message": "Sign-in is not available right now."}, status=500)

    user, created = _get_or_create_user(sub, email, name)
    if not user.is_active:
        return JsonResponse({"ok": False, "message": "This account is disabled."}, status=403)

    # The cart lives in the session, and login() keeps it, so a guest's cart follows them in.
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return JsonResponse({"ok": True, "redirect": _safe_next(request, body.get("next")), "new": created})


@require_POST
def logout_view(request):
    logout(request)
    return redirect("store:home")


@login_required
def my_orders(request):
    orders = request.user.orders.prefetch_related("items")
    return render(request, "accounts/orders.html", {"orders": orders})