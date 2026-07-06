"""Web Push delivery: gate by prefs, send via pywebpush, prune dead subscriptions."""
import base64
import json
import logging
from functools import lru_cache
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from pywebpush import webpush, WebPushException
from app.core.config import settings

logger = logging.getLogger("uvicorn.error")

DEFAULT_PREFS = {"master": True, "important": True, "reminders": True, "digest": True}


@lru_cache(maxsize=1)
def vapid_private_key_for_push() -> str:
    """The private key in the form pywebpush's string argument expects.

    The env stores a PKCS8 PEM (with escaped newlines), but pywebpush treats a
    string as the raw base64url EC private scalar — handing it a PEM raises a
    deserialization error. Convert the PEM to that raw scalar; pass through a
    value that is already raw.
    """
    raw = (settings.VAPID_PRIVATE_KEY or "").replace("\\n", "\n")
    if "BEGIN" not in raw:
        return raw
    key = load_pem_private_key(raw.encode(), password=None)
    scalar = key.private_numbers().private_value.to_bytes(32, "big")
    return base64.urlsafe_b64encode(scalar).rstrip(b"=").decode()


def _prefs_for(client, user_id: str) -> dict:
    try:
        res = client.table("profiles").select("notification_prefs").eq("id", user_id).execute()
        if res.data:
            return {**DEFAULT_PREFS, **(res.data[0].get("notification_prefs") or {})}
    except Exception as e:
        logger.warning(f"notification_prefs load failed for {user_id}: {e}")
    return dict(DEFAULT_PREFS)


def _send_one(sub: dict, payload: dict) -> None:
    """Send one push. Raises WebPushException on transport failure."""
    webpush(
        subscription_info={
            "endpoint": sub["endpoint"],
            "keys": {"p256dh": sub["p256dh"], "auth": sub["auth"]},
        },
        data=json.dumps(payload),
        vapid_private_key=vapid_private_key_for_push(),
        vapid_claims={"sub": settings.VAPID_SUBJECT},
    )


def send_to_user(client, user_id: str, payload: dict, kind: str | None = None) -> int:
    """Push `payload` to the user's subscriptions if prefs allow. Returns count sent.

    kind=None gates on the master toggle only (used by the test notification);
    a string kind additionally requires that per-kind toggle to be on.
    """
    if not settings.VAPID_PRIVATE_KEY:
        return 0
    prefs = _prefs_for(client, user_id)
    if not prefs.get("master"):
        return 0
    if kind is not None and not prefs.get(kind):
        return 0
    try:
        subs = client.table("push_subscriptions").select("*").eq("user_id", user_id).execute().data or []
    except Exception as e:
        logger.warning(f"subscription load failed for {user_id}: {e}")
        return 0

    sent = 0
    for sub in subs:
        try:
            _send_one(sub, payload)
            sent += 1
        except WebPushException as e:
            code = getattr(getattr(e, "response", None), "status_code", None)
            if code in (404, 410):
                try:
                    client.table("push_subscriptions").delete().eq("endpoint", sub["endpoint"]).execute()
                except Exception as del_err:
                    logger.warning(f"failed to prune dead subscription: {del_err}")
            else:
                logger.warning(f"push failed (endpoint kept): {e}")
        except Exception as e:
            logger.warning(f"push error: {e}")
    return sent
