"""Tests for MCP response trimming helpers in util.py."""
# pyright: reportMissingImports=false

import json
import pytest

pytestmark = pytest.mark.structure


class TestMinifyJson:
    def test_pretty_json_is_minified(self, add_agent_to_path):
        from util import minify_json
        pretty = json.dumps({"a": 1, "b": [1, 2, 3]}, indent=2)
        out = minify_json(pretty)
        assert out == '{"a":1,"b":[1,2,3]}'

    def test_non_json_passes_through_unchanged(self, add_agent_to_path):
        from util import minify_json
        text = "not json, just a plain string"
        assert minify_json(text) == text


class TestTruncateResponse:
    def test_short_text_is_unchanged(self, add_agent_to_path):
        from util import truncate_response
        text = "small payload"
        assert truncate_response(text, max_chars=100) == text

    def test_oversized_text_is_truncated_with_marker(self, add_agent_to_path):
        from util import truncate_response
        text = "x" * 500
        out = truncate_response(text, max_chars=100)
        assert out.endswith("...[truncated]")

    def test_default_cap_is_modest(self, add_agent_to_path):
        from util import MCP_MAX_RESPONSE_CHARS
        assert MCP_MAX_RESPONSE_CHARS <= 50_000
