import os
import subprocess

from httpie.output.ui import man_pages


def test_is_available_short_circuits_on_windows(monkeypatch):
    monkeypatch.setattr(os, "name", "nt")
    monkeypatch.setattr(man_pages, "NO_MAN_PAGES", False)

    calls = []

    def track(*a, **k):
        calls.append((a, k))
        return subprocess.CompletedProcess(args=a[0] if a else None, returncode=0)

    monkeypatch.setattr(subprocess, "run", track)
    # Also patch the reference used inside the module, if any.
    monkeypatch.setattr(man_pages, "subprocess", subprocess)

    assert man_pages.is_available("http") is False
    assert calls == [], "subprocess.run must not be called on Windows"


def test_is_available_honors_NO_MAN_PAGES(monkeypatch):
    monkeypatch.setattr(man_pages, "NO_MAN_PAGES", True)
    assert man_pages.is_available("http") is False
