"""Utility functions for MCP tool processing."""
import asyncio
import hashlib
import json
import logging
import os
import re
from typing import Any

import httpx
from langchain_core.tools import ToolException

logger = logging.getLogger(__name__)

_MCP_RETRY_ATTEMPTS = 4
_MCP_RETRY_DELAY = 4.0
MCP_CALL_TIMEOUT_SECONDS = float(os.environ.get("MCP_CALL_TIMEOUT_SECONDS", 30.0))
MCP_MAX_RESPONSE_CHARS = int(os.environ.get("MCP_MAX_RESPONSE_CHARS", 30_000))


def minify_json(text: str) -> str:
    try:
        parsed = json.loads(text)
    except (ValueError, TypeError):
        return text
    return json.dumps(parsed, separators=(",", ":"), ensure_ascii=False)


def truncate_response(text: str, max_chars: int = MCP_MAX_RESPONSE_CHARS) -> str:
    if len(text) <= max_chars:
        return text
    window = text[:max_chars]
    floor = int(max_chars * 0.9)
    boundary = max(window.rfind("\n"), window.rfind(","), window.rfind(" "))
    if boundary >= floor:
        window = window[:boundary]
    return window + "\n...[truncated]"


def _is_retryable_error(exc: Exception) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code < 400 or exc.response.status_code >= 500
    if isinstance(exc, (ExceptionGroup, BaseExceptionGroup)):
        return True
    if isinstance(exc, (asyncio.TimeoutError, TimeoutError)):
        return True
    return True


def enhance_tool_description(mcp_tool: Any) -> str:
    if mcp_tool is None:
        logger.warning("enhance_tool_description called with None tool")
        return ""
    server_label = getattr(mcp_tool, "fragment_name", mcp_tool.server_name)
    enhanced_description = f"[{server_label}] {mcp_tool.description or ''}".strip()
    return enhanced_description


def enhance_tool_name(mcp_tool: Any) -> str:
    if mcp_tool is None:
        logger.warning("enhance_tool_name called with None tool")
        return ""
    server_name = mcp_tool.server_name
    tool_name = mcp_tool.name
    segments = server_name.split(":")
    if len(segments) > 2:
        remaining = segments[2:]
    else:
        remaining = segments
    server_part = "_".join(remaining)
    raw = f"{server_part}__{tool_name}"
    sanitized = re.sub(r"[^a-zA-Z0-9\-_]", "_", raw)
    if len(sanitized) <= 64:
        return sanitized
    suffix = hashlib.sha256(sanitized.encode()).hexdigest()[:8]
    return f"{sanitized[:55]}_{suffix}"


async def call_mcp_tool_with_retry(agw_client: Any, mcp_tool: Any, user_token: Any = None, **kwargs: Any) -> str:
    if mcp_tool is None:
        raise ValueError("Tool parameter cannot be None")

    last_exc: Exception | None = None
    for attempt in range(1 + _MCP_RETRY_ATTEMPTS):
        try:
            arg_keys = list(kwargs.keys()) if kwargs else []
            logger.info(f"Calling MCP tool '{mcp_tool.name}' via Agent Gateway with {len(arg_keys)} argument(s)")

            _call_result = None
            try:
                call_params = {"tool": mcp_tool, **kwargs}
                if user_token is not None:
                    call_params["user_token"] = user_token
                _call_result = await asyncio.wait_for(
                    agw_client.call_mcp_tool(**call_params),
                    timeout=MCP_CALL_TIMEOUT_SECONDS,
                )
            except (asyncio.TimeoutError, TimeoutError):
                logger.warning(f"call_mcp_tool_with_retry: Tool {mcp_tool.name} timed out after {MCP_CALL_TIMEOUT_SECONDS}s")
                raise
            except (ExceptionGroup, BaseExceptionGroup) as eg:
                if _call_result is None:
                    raise
                logger.debug(f"Ignoring ExceptionGroup on teardown for {mcp_tool.name}: {eg}")

            if _call_result is None:
                raise RuntimeError(f"SDK call_mcp_tool returned None for {mcp_tool.name}")

            result = str(_call_result) if _call_result else ""
            result = minify_json(result)
            if len(result) > MCP_MAX_RESPONSE_CHARS:
                logger.warning(f"Response from {mcp_tool.name} truncated from {len(result)} to ~{MCP_MAX_RESPONSE_CHARS} chars")
                result = truncate_response(result, MCP_MAX_RESPONSE_CHARS)

            logger.info(f"MCP tool '{mcp_tool.name}' returned successfully (response length: {len(result)} chars)")
            return result

        except Exception as e:
            if not _is_retryable_error(e):
                raise
            last_exc = e
            if attempt < _MCP_RETRY_ATTEMPTS:
                logger.warning(f"Error calling {mcp_tool.name} (attempt {attempt + 1}/{1 + _MCP_RETRY_ATTEMPTS}), retrying: {e}")
                await asyncio.sleep(_MCP_RETRY_DELAY)

    raise ToolException(f"Tool '{mcp_tool.name}' failed after {1 + _MCP_RETRY_ATTEMPTS} attempts: {last_exc}") from last_exc
