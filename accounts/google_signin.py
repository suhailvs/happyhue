"""Server side check of a Google sign-in. The browser only hands us an ID token;
nothing is trusted until verify_google_token has validated it against Google's keys."""
import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

log = logging.getLogger(__name__)


class GoogleAuthFailed(Exception):
    """The token is missing, invalid, expired, or has no verified email."""


def verify_google_token(token):
    """Return (google_sub, email, name) for a valid Google ID token."""
    client_id = getattr(settings, "GOOGLE_CLIENT_ID", "")
    if not client_id:
        raise ImproperlyConfigured("Set GOOGLE_CLIENT_ID.")
    if not token or not isinstance(token, str):
        raise GoogleAuthFailed("Missing token.")
    try:
        info = id_token.verify_oauth2_token(
            token, google_requests.Request(), client_id, clock_skew_in_seconds=10
        )
    except (ValueError, GoogleAuthError) as exc:
        log.info("Google token rejected: %s", exc)
        raise GoogleAuthFailed("Invalid or expired token.") from exc

    sub, email = info.get("sub"), (info.get("email") or "").strip().lower()
    if not sub or not email:
        raise GoogleAuthFailed("Google did not return an email address.")
    if not info.get("email_verified"):
        raise GoogleAuthFailed("Your Google email address is not verified.")
    return sub, email, (info.get("name") or "").strip()