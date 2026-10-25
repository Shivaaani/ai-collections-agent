"""Model calls through the Claude Code CLI (`claude -p`), billed to a Claude subscription instead of API credits.

Each call is stateless: the caller renders the whole conversation into the prompt. Claude Code's own tools,
MCP servers and slash commands are switched off, and our system prompt replaces its default one.
"""

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

# An empty working directory, so Claude Code picks up no project files or CLAUDE.md.
_CWD = Path(tempfile.gettempdir()) / "collections-agent-cli"


class CliError(RuntimeError):
    pass


class UsageLimitReached(CliError):
    pass


@dataclass
class CliUsage:
    """Same fields as the SDK's usage object, so cost and token reporting work for both backends."""

    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0


def complete(
    system: str,
    prompt: str,
    model: str,
    effort: str | None = None,
    json_schema: dict | None = None,
    timeout: int = 300,
):
    """Run one model call. Returns (text, usage), or (parsed JSON, usage) when json_schema is given."""
    cmd = [
        "claude", "-p",
        "--model", model,
        "--tools", "",
        "--strict-mcp-config",
        "--disable-slash-commands",
        "--no-session-persistence",
        "--system-prompt", system,
        "--output-format", "json",
    ]
    if effort:
        cmd += ["--effort", effort]
    if json_schema:
        cmd += ["--json-schema", json.dumps(json_schema)]

    # Without an API key in the environment, Claude Code uses the logged-in subscription.
    env = {k: v for k, v in os.environ.items() if k not in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")}
    _CWD.mkdir(exist_ok=True)
    proc = subprocess.run(
        cmd, input=prompt, capture_output=True, text=True, env=env, cwd=_CWD, timeout=timeout
    )
    try:
        out = json.loads(proc.stdout)
    except json.JSONDecodeError:
        raise CliError(f"claude -p failed (exit {proc.returncode}): {(proc.stderr or proc.stdout)[:500]}") from None

    u = out.get("usage") or {}
    usage = CliUsage(
        model=model,
        input_tokens=u.get("input_tokens", 0),
        output_tokens=u.get("output_tokens", 0),
        cache_read_input_tokens=u.get("cache_read_input_tokens", 0),
        cache_creation_input_tokens=u.get("cache_creation_input_tokens", 0),
    )
    if out.get("is_error"):
        message = str(out.get("result") or out.get("subtype"))
        if "limit" in message.lower():
            raise UsageLimitReached(message)
        raise CliError(message)
    if json_schema:
        if out.get("structured_output") is None:
            raise CliError("No structured output returned.")
        return out["structured_output"], usage
    return (out.get("result") or "").strip(), usage
