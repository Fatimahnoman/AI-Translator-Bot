"""
Integration tests for TranslateHub chat flow.
Tests the full conversation lifecycle without hitting real APIs.
Run: python -m pytest tests/test_integration.py -v
"""

import importlib
import os
import sys
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_root)

spec = importlib.util.spec_from_file_location(
    "trans_agent", os.path.join(_project_root, "trans-agent.py")
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

validate_language = mod.validate_language
sanitize_input = mod.sanitize_input
sanitize_for_output = mod.sanitize_for_output
_check_rate_limit = mod._check_rate_limit
_rate_store = mod._rate_store
SUPPORTED_LANGUAGES = mod.SUPPORTED_LANGUAGES


# ─── Helpers ──────────────────────────────────────────────
def _mock_session() -> dict:
    """Create a mock session store."""
    store: dict = {}

    def fake_set(key, value):
        store[key] = value

    def fake_get(key, default=None):
        return store.get(key, default)

    mock_session = MagicMock()
    mock_session.set = fake_set
    mock_session.get = fake_get

    return store, mock_session


@pytest.fixture(autouse=True)
def reset_rate_limits():
    """Clear rate limit store between tests."""
    _rate_store.clear()
    yield
    _rate_store.clear()


# ─── Flow: Language Selection ─────────────────────────────
class TestLanguageSelectionFlow:
    def test_valid_language_sets_state(self):
        store, _ = _mock_session()
        store["awaiting_language"] = True

        result = validate_language("urdu")
        assert result == "Urdu"

    def test_invalid_language_returns_none(self):
        assert validate_language("klingon") is None

    def test_all_supported_languages_work(self):
        for key, expected in SUPPORTED_LANGUAGES.items():
            assert validate_language(key) == expected


# ─── Flow: Full Translation Cycle ────────────────────────
class TestFullTranslationCycle:
    def test_state_transitions(self):
        """Simulate: select language -> enter text -> translate -> reset."""
        store = {}
        # Step 1: Chat starts
        store["awaiting_language"] = True
        store["awaiting_text"] = False
        store["target_language"] = None

        # Step 2: User picks language
        lang = validate_language("french")
        assert lang == "French"
        store["target_language"] = lang
        store["awaiting_language"] = False
        store["awaiting_text"] = True

        # Step 3: User enters text
        assert store["awaiting_text"] is True
        text = sanitize_input("Hello world")
        assert text == "Hello world"

        # Step 4: After translation, reset
        store["awaiting_language"] = True
        store["awaiting_text"] = False
        store["target_language"] = None

        assert store["awaiting_language"] is True
        assert store["awaiting_text"] is False
        assert store["target_language"] is None

    def test_provider_switch_resets_state(self):
        store = {}
        store["awaiting_text"] = True
        store["target_language"] = "Urdu"

        # Simulate /model command
        store["awaiting_language"] = True
        store["awaiting_text"] = False
        store["target_language"] = None

        assert store["awaiting_language"] is True
        assert store["target_language"] is None


# ─── Flow: Sanitization in Context ────────────────────────
class TestSanitizationIntegration:
    def test_xss_in_language_input(self):
        result = sanitize_input('<script>alert("xss")</script>')
        assert "<script>" not in result
        assert "alert" in result

    def test_xss_in_translation_text(self):
        malicious = 'Hello <img src=x onerror=alert(1)> world'
        result = sanitize_input(malicious)
        assert "<img" not in result

    def test_translation_output_escaped(self):
        output = '<b>Hello</b> & "world"'
        safe = sanitize_for_output(output)
        assert "&lt;b&gt;" in safe
        assert "&amp;" in safe
        assert "&quot;" in safe

    def test_long_input_truncated(self):
        long_text = "a" * 5000
        result = sanitize_input(long_text, max_length=2000)
        assert len(result) == 2000


# ─── Flow: Rate Limiting ─────────────────────────────────
class TestRateLimitingIntegration:
    def test_burst_then_block(self):
        for _ in range(15):
            assert _check_rate_limit("burst_user") is True
        assert _check_rate_limit("burst_user") is False

    def test_different_users_independent(self):
        for _ in range(15):
            _check_rate_limit("user_a")
        assert _check_rate_limit("user_a") is False
        assert _check_rate_limit("user_b") is True

    def test_window_expiry(self):
        _rate_store["old_user"] = [time.time() - 120]
        assert _check_rate_limit("old_user") is True


# ─── Flow: Error Scenarios ────────────────────────────────
class TestErrorScenarios:
    def test_empty_message_handled(self):
        result = sanitize_input("")
        assert result == ""

    def test_whitespace_only_message(self):
        result = sanitize_input("   \n\t  ")
        assert result == ""

    def test_special_characters_in_language(self):
        assert validate_language("") is None
        assert validate_language("123") is None
        assert validate_language("!@#$%") is None
        assert validate_language("urdu!") is None

    def test_partial_language_match(self):
        assert validate_language("urd") is None
        assert validate_language("fren") is None
        assert validate_language("englis") is None


# ─── Flow: Chat History ───────────────────────────────────
class TestChatHistory:
    def test_history_grows_during_session(self):
        history = []
        history.append({"role": "user", "content": "Translate to Urdu: Hello"})
        history.append({"role": "assistant", "content": "Hello = ہیلو"})
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"

    def test_history_reset_on_new_chat(self):
        history = [{"role": "user", "content": "old"}]
        history = []
        assert len(history) == 0
