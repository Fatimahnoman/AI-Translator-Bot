"""
Unit tests for TranslateHub core functions.
Run: python -m pytest tests/ -v
"""

import time
import sys
import os

import importlib

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_root)

spec = importlib.util.spec_from_file_location("trans_agent", os.path.join(_project_root, "trans-agent.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

validate_language = mod.validate_language
sanitize_input = mod.sanitize_input
sanitize_for_output = mod.sanitize_for_output
_check_rate_limit = mod._check_rate_limit
_rate_store = mod._rate_store


# ─── Language Validation ──────────────────────────────────
class TestValidateLanguage:
    def test_valid_languages(self):
        for key, expected in [
            ("urdu", "Urdu"),
            ("english", "English"),
            ("arabic", "Arabic"),
            ("french", "French"),
            ("japanese", "Japanese"),
            ("korean", "Korean"),
        ]:
            assert validate_language(key) == expected

    def test_case_insensitive(self):
        assert validate_language("URDU") == "Urdu"
        assert validate_language("UrDu") == "Urdu"
        assert validate_language("  french  ") == "French"

    def test_invalid_language(self):
        assert validate_language("klingon") is None
        assert validate_language("python") is None
        assert validate_language("") is None

    def test_title_case_output(self):
        assert validate_language("urdu") == "Urdu"
        assert validate_language("portuguese") == "Portuguese"


# ─── Sanitization ─────────────────────────────────────────
class TestSanitizeInput:
    def test_strips_html_tags(self):
        assert sanitize_input("<script>alert('xss')</script>") == "alert(&#x27;xss&#x27;)"
        assert sanitize_input("<b>hello</b>") == "hello"

    def test_escapes_entities(self):
        assert sanitize_input("hello & goodbye") == "hello &amp; goodbye"
        # < b > gets stripped as an HTML tag (correct behavior)
        assert sanitize_input("a < b > c") == "a  c"

    def test_enforces_max_length(self):
        long_text = "a" * 5000
        assert len(sanitize_input(long_text, max_length=100)) == 100

    def test_strips_whitespace(self):
        assert sanitize_input("  hello  ") == "hello"

    def test_preserves_normal_text(self):
        assert sanitize_input("Translate to Urdu") == "Translate to Urdu"

    def test_empty_input(self):
        assert sanitize_input("") == ""


class TestSanitizeForOutput:
    def test_escapes_html(self):
        assert "&lt;" in sanitize_for_output("<div>test</div>")

    def test_enforces_max_length(self):
        long_text = "x" * 10000
        assert len(sanitize_for_output(long_text, max_length=100)) == 100

    def test_preserves_normal_text(self):
        text = "Hello, this is a translation."
        assert sanitize_for_output(text) == text


# ─── Rate Limiting ────────────────────────────────────────
class TestRateLimiting:
    def test_allows_within_limit(self):
        _rate_store["test_user"] = []
        for _ in range(RATE_LIMIT_MAX - 1):
            assert _check_rate_limit("test_user") is True

    def test_blocks_over_limit(self):
        _rate_store["test_user_full"] = [time.time()] * RATE_LIMIT_MAX
        assert _check_rate_limit("test_user_full") is False

    def test_resets_after_window(self):
        _rate_store["test_user_expire"] = [time.time() - RATE_LIMIT_WINDOW - 1]
        assert _check_rate_limit("test_user_expire") is True

    def test_independent_users(self):
        _rate_store["user_a"] = [time.time()] * RATE_LIMIT_MAX
        _rate_store["user_b"] = []
        assert _check_rate_limit("user_a") is False
        assert _check_rate_limit("user_b") is True


# Constants for rate limit tests
RATE_LIMIT_MAX = 15
RATE_LIMIT_WINDOW = 60
