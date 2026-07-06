"""send_to_user prefs gating, including the master-only (kind=None) test path."""
import app.services.push as push


class _FakeTable:
    def __init__(self, rows):
        self._rows = rows
    def select(self, *a, **k):
        return self
    def eq(self, *a, **k):
        return self
    def execute(self):
        return type("R", (), {"data": self._rows})()


def _client_with_subs(subs):
    return type("C", (), {"table": lambda self, n: _FakeTable(subs)})()


def _setup(monkeypatch, prefs, subs):
    monkeypatch.setattr(push.settings, "VAPID_PRIVATE_KEY", "priv")
    monkeypatch.setattr(push, "_prefs_for", lambda client, uid: prefs)
    sent = []
    monkeypatch.setattr(push, "_send_one", lambda sub, payload: sent.append(sub))
    return sent


def test_kind_none_sends_when_master_on_ignoring_per_kind(monkeypatch):
    # important toggled OFF, but kind=None must still send (master is on).
    prefs = {"master": True, "important": False, "reminders": False, "digest": False}
    subs = [{"endpoint": "e1", "p256dh": "a", "auth": "b"}]
    sent = _setup(monkeypatch, prefs, subs)
    n = push.send_to_user(_client_with_subs(subs), "u1", {"title": "x"}, None)
    assert n == 1 and len(sent) == 1


def test_kind_none_blocked_when_master_off(monkeypatch):
    prefs = {"master": False, "important": True, "reminders": True, "digest": True}
    subs = [{"endpoint": "e1", "p256dh": "a", "auth": "b"}]
    sent = _setup(monkeypatch, prefs, subs)
    n = push.send_to_user(_client_with_subs(subs), "u1", {"title": "x"}, None)
    assert n == 0 and len(sent) == 0


def test_string_kind_still_gated_per_kind(monkeypatch):
    prefs = {"master": True, "important": False, "reminders": True, "digest": True}
    subs = [{"endpoint": "e1", "p256dh": "a", "auth": "b"}]
    sent = _setup(monkeypatch, prefs, subs)
    n = push.send_to_user(_client_with_subs(subs), "u1", {"title": "x"}, "important")
    assert n == 0 and len(sent) == 0
