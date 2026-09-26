"""Static route table for local-first inference.

Task classes are configuration, not Warden policy.
Changing a route never mutates canonical Phoenix state.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Backend:
    name: str
    kind: str  # ollama | vllm | openai_compat | cloud
    base_url: str
    model: str
    max_concurrent: int = 1
    timeout_s: float = 120.0


DEFAULT_BACKENDS = {
    "ollama_chat": Backend(
        name="ollama_chat",
        kind="ollama",
        base_url="http://127.0.0.1:11434/v1",
        model="llama3.1:8b",
        max_concurrent=2,
    ),
    "ollama_code": Backend(
        name="ollama_code",
        kind="ollama",
        base_url="http://127.0.0.1:11434/v1",
        model="qwen2.5-coder:7b",
        max_concurrent=1,
    ),
    "ollama_embed": Backend(
        name="ollama_embed",
        kind="ollama",
        base_url="http://127.0.0.1:11434/v1",
        model="nomic-embed-text",
        max_concurrent=4,
        timeout_s=30.0,
    ),
    "vllm": Backend(
        name="vllm",
        kind="vllm",
        base_url="http://127.0.0.1:8000/v1",
        model="local-vllm",
        max_concurrent=4,
    ),
    "cloud": Backend(
        name="cloud",
        kind="cloud",
        base_url="https://api.openai.com/v1",
        model="gpt-4o-mini",
        max_concurrent=8,
        timeout_s=60.0,
    ),
}


# First listed backend is preferred. Cloud is last and requires opt-in.
TASK_ROUTES = {
    "chat": ("ollama_chat", "vllm", "cloud"),
    "code": ("ollama_code", "vllm", "cloud"),
    "embed": ("ollama_embed",),
    "long_context": ("vllm", "ollama_chat", "cloud"),
}
