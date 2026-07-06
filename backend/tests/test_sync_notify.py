"""maybe_notify sync-time gate: important OR interest-match."""
import app.tasks.sync_task as st


class _EventsTable:
    """Records every payload passed to .update() on a shared list so tests
    can assert whether (and what) an update actually happened."""
    def __init__(self, recorder):
        self._recorder = recorder
    def update(self, payload=None, *a, **k):
        self._recorder.append(payload)
        return self
    def eq(self, *a, **k):
        return self
    def execute(self):
        return type("R", (), {"data": []})()


def _make_client(recorder):
    return type("C", (), {"table": lambda self, n: _EventsTable(recorder)})()


_CLIENT = _make_client([])


def _patch(monkeypatch, priority, raise_on_send=False):
    monkeypatch.setattr(st, "calculate_priority", lambda ev, slugs: priority)
    calls = []

    def _send(c, u, p, k):
        if raise_on_send:
            raise RuntimeError("boom")
        calls.append((p, k))
        return 1

    monkeypatch.setattr(st, "send_to_user", _send)
    return calls


def test_interest_match_below_threshold_notifies(monkeypatch):
    calls = _patch(monkeypatch, priority=40.0)  # below IMPORTANT_THRESHOLD (60)
    ev = {"id": "e1", "display_name": "Cultural fest", "raw_summary": "s",
          "interest_tags": ["cultural"], "notified_at": None}
    assert st.maybe_notify(_CLIENT, "u1", ev, ["cultural", "music"]) is True
    assert len(calls) == 1


def test_no_match_below_threshold_stays_silent(monkeypatch):
    calls = _patch(monkeypatch, priority=40.0)
    ev = {"id": "e2", "display_name": "Mess menu", "raw_summary": "s",
          "interest_tags": ["food-committee"], "notified_at": None}
    assert st.maybe_notify(_CLIENT, "u1", ev, ["cultural", "music"]) is False
    assert calls == []


def test_empty_interests_below_threshold_stays_silent(monkeypatch):
    calls = _patch(monkeypatch, priority=40.0)
    ev = {"id": "e3", "display_name": "x", "raw_summary": "s",
          "interest_tags": ["cultural"], "notified_at": None}
    assert st.maybe_notify(_CLIENT, "u1", ev, []) is False
    assert calls == []


def test_important_above_threshold_notifies_without_match(monkeypatch):
    calls = _patch(monkeypatch, priority=75.0)
    ev = {"id": "e4", "display_name": "Placement", "raw_summary": "s",
          "interest_tags": [], "notified_at": None}
    assert st.maybe_notify(_CLIENT, "u1", ev, ["cultural"]) is True
    assert len(calls) == 1


def test_match_is_case_insensitive(monkeypatch):
    calls = _patch(monkeypatch, priority=10.0)
    ev = {"id": "e5", "display_name": "y", "raw_summary": "s",
          "interest_tags": ["Cultural"], "notified_at": None}
    assert st.maybe_notify(_CLIENT, "u1", ev, ["cultural"]) is True
    assert len(calls) == 1


def test_already_notified_event_skips_and_does_not_send(monkeypatch):
    # Even a would-otherwise-notify priority must not fire a second push.
    calls = _patch(monkeypatch, priority=75.0)
    updates = []
    client = _make_client(updates)
    ev = {"id": "e6", "display_name": "Placement", "raw_summary": "s",
          "interest_tags": [], "notified_at": "2026-07-01T00:00:00Z"}
    assert st.maybe_notify(client, "u1", ev, ["cultural"]) is False
    assert calls == []
    assert updates == []


def test_send_failure_is_swallowed_and_does_not_stamp(monkeypatch):
    calls = _patch(monkeypatch, priority=75.0, raise_on_send=True)
    updates = []
    client = _make_client(updates)
    ev = {"id": "e7", "display_name": "Placement", "raw_summary": "s",
          "interest_tags": [], "notified_at": None}
    assert st.maybe_notify(client, "u1", ev, ["cultural"]) is False
    assert calls == []
    assert updates == []
