"""Tests for state.py — In-memory session state."""
import pytest
from state import SessionManager


class TestSessionManager:
    def test_get_creates_default(self):
        sm = SessionManager()
        s = sm.get(123)
        assert s["step"] is None
        assert s["method"] is None
        assert s["cover"] is None
        assert s["encrypt"] is False

    def test_update(self):
        sm = SessionManager()
        sm.update(123, step="awaiting_cover", method="zwc")
        s = sm.get(123)
        assert s["step"] == "awaiting_cover"
        assert s["method"] == "zwc"

    def test_reset(self):
        sm = SessionManager()
        sm.update(123, step="awaiting_secret")
        sm.reset(123)
        s = sm.get(123)
        assert s["step"] is None

    def test_is_encoding(self):
        sm = SessionManager()
        assert sm.is_encoding(123) is False
        sm.update(123, step="awaiting_cover")
        assert sm.is_encoding(123) is True

    def test_is_encoding_after_reset(self):
        sm = SessionManager()
        sm.update(123, step="awaiting_cover")
        sm.reset(123)
        assert sm.is_encoding(123) is False
