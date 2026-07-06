"""The VAPID private key handed to pywebpush must be deserializable by it.

Regression for the silent push failure: the env stores a PKCS8 PEM (with
escaped newlines), but pywebpush's string argument must be the raw base64url
EC private scalar. Passing the PEM string made pywebpush raise
ValueError (ASN.1 parsing error), which send_to_user swallowed -> sent=0.
"""
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from py_vapid import Vapid02

import app.services.push as push


def _pkcs8_pem_escaped() -> str:
    """A real P-256 PKCS8 PEM with newlines escaped, exactly how the env stores it."""
    priv = ec.generate_private_key(ec.SECP256R1())
    pem = priv.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    return pem.replace("\n", "\\n")


def test_pem_string_is_not_directly_consumable_by_pywebpush():
    """Guard the premise: pywebpush cannot deserialize a PKCS8 PEM string directly."""
    pem = _pkcs8_pem_escaped().replace("\\n", "\n")
    import pytest
    with pytest.raises(ValueError):
        Vapid02.from_string(pem)


def test_vapid_private_key_helper_is_consumable_by_pywebpush(monkeypatch):
    monkeypatch.setattr(push.settings, "VAPID_PRIVATE_KEY", _pkcs8_pem_escaped())
    push.vapid_private_key_for_push.cache_clear()
    key_str = push.vapid_private_key_for_push()
    # Must not raise — this is exactly what pywebpush does with the string arg.
    Vapid02.from_string(key_str)


def test_helper_passes_through_already_raw_key(monkeypatch):
    """If a raw base64url key is ever stored, return it unchanged."""
    priv = ec.generate_private_key(ec.SECP256R1())
    import base64
    scalar = priv.private_numbers().private_value.to_bytes(32, "big")
    raw = base64.urlsafe_b64encode(scalar).rstrip(b"=").decode()
    monkeypatch.setattr(push.settings, "VAPID_PRIVATE_KEY", raw)
    push.vapid_private_key_for_push.cache_clear()
    assert push.vapid_private_key_for_push() == raw
