"""Server side check of a Firebase phone sign-in. The browser only proves who it is with an ID token;
nothing is trusted until verify_phone_token has validated it against Google's keys."""
import json
import logging
import time

import firebase_admin
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from firebase_admin import auth, credentials
from firebase_admin.exceptions import FirebaseError

log = logging.getLogger(__name__)

MAX_TOKEN_AGE = 300  # seconds since the OTP was entered; an older token is not accepted for sign-in


class FirebaseAuthError(Exception):
    """The token is missing, invalid, expired or not from a phone sign-in."""


def _app():
    try:
        return firebase_admin.get_app()
    except ValueError:
        pass
    raw = getattr(settings, "FIREBASE_CREDENTIALS_JSON", "")
    path = getattr(settings, "FIREBASE_CREDENTIALS_FILE", "")
    if raw:
        cred = credentials.Certificate(json.loads(raw))
    elif path:
        cred = credentials.Certificate(path)
    else:
        raise ImproperlyConfigured("Set FIREBASE_CREDENTIALS_FILE or FIREBASE_CREDENTIALS_JSON.")
    return firebase_admin.initialize_app(cred)


def verify_phone_token(id_token):
    """Return (firebase_uid, phone_number) for a valid, recent phone sign-in token."""
    if not id_token or not isinstance(id_token, str):
        raise FirebaseAuthError("Missing token.")
    try:
        decoded = auth.verify_id_token(id_token, app=_app(), clock_skew_seconds=10)
    except (ValueError, FirebaseError) as exc:
        log.info("Firebase token rejected: %s", exc)
        raise FirebaseAuthError("Invalid or expired token.") from exc

    if decoded.get("firebase", {}).get("sign_in_provider") != "phone":
        raise FirebaseAuthError("Not a phone sign-in.")
    phone, uid = decoded.get("phone_number"), decoded.get("uid")
    if not phone or not uid:
        raise FirebaseAuthError("Token has no phone number.")
    if time.time() - decoded.get("auth_time", 0) > MAX_TOKEN_AGE:
        raise FirebaseAuthError("Sign-in is too old. Please request a new code.")
    return uid, phone
