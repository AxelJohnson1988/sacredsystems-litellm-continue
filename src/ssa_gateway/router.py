"""Local-first model router.

Boundary:
- This module selects a backend and issues an OpenAI-compatible chat/embed call.
- It does not authorize, commit, hash-chain, or issue receipts.
- Callers that need a commitment must go through Warden.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping
import json
import os
import urllib.error
import urllib.request

from .routes import DEFAULT_BACKENDS, TASK_ROUTES, Backend


class CloudDisabledError(RuntimeError):
    pass


class NoBackendAvailable(RuntimeError):
    pass


@dataclass(frozen=True)
class RouteDecision:
    task_class: str
    backend_name: str
    backend_kind: str
    model: str
    base_url: str
    attempted: tuple[str, ...]
    cloud_allowed: bool


@dataclass(frozen=True)
class InferenceResult:
    decision: RouteDecision
    content: str
    raw: Mapping[str, Any] = field(default_factory=dict)
    is_receipt: bool = False  # always False; kept explicit for boundary tests


HttpPost = Callable[[str, dict[str, Any], dict[str, str], float], dict[str, Any]]


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _default_http_post(url: str, payload: dict[str, Any], headers: dict[str, str], timeout_s: float) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"http {exc.code} from {url}: {detail[:300]}") from exc


class GatewayRouter:
    def __init__(
        self,
        backends: Mapping[str, Backend] | None = None,
        routes: Mapping[str, tuple[str, ...]] | None = None,
        http_post: HttpPost | None = None,
        allow_cloud: bool | None = None,
    ) -> None:
        self._backends = dict(backends or DEFAULT_BACKENDS)
        self._routes = dict(routes or TASK_ROUTES)
        self._http_post = http_post or _default_http_post
        self._allow_cloud = _env_flag("SSA_ALLOW_CLOUD") if allow_cloud is None else allow_cloud

    def decide(self, task_class: str) -> RouteDecision:
        if task_class not in self._routes:
            raise ValueError(f"unknown-task-class:{task_class}")
        chain = self._routes[task_class]
        attempted: list[str] = []
        chosen: Backend | None = None
        for name in chain:
            backend = self._backends[name]
            attempted.append(name)
            if backend.kind == "cloud" and not self._allow_cloud:
                continue
            chosen = backend
            break
        if chosen is None:
            raise CloudDisabledError(
                "cloud backend is the only remaining option; set SSA_ALLOW_CLOUD=1 to enable"
            )
        return RouteDecision(
            task_class=task_class,
            backend_name=chosen.name,
            backend_kind=chosen.kind,
            model=chosen.model,
            base_url=chosen.base_url,
            attempted=tuple(attempted),
            cloud_allowed=self._allow_cloud,
        )

    def chat(self, messages: list[dict[str, str]], task_class: str = "chat") -> InferenceResult:
        decision = self.decide(task_class)
        backend = self._backends[decision.backend_name]
        url = decision.base_url.rstrip("/") + "/chat/completions"
        payload = {"model": decision.model, "messages": messages}
        headers = {"Content-Type": "application/json"}
        api_key = os.environ.get("SSA_GATEWAY_API_KEY") or os.environ.get("OPENAI_API_KEY")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        raw = self._http_post(url, payload, headers, backend.timeout_s)
        content = ""
        try:
            content = raw["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            content = json.dumps(raw)
        return InferenceResult(decision=decision, content=content, raw=raw, is_receipt=False)

    def embed(self, text: str) -> InferenceResult:
        decision = self.decide("embed")
        backend = self._backends[decision.backend_name]
        url = decision.base_url.rstrip("/") + "/embeddings"
        payload = {"model": decision.model, "input": text}
        headers = {"Content-Type": "application/json"}
        raw = self._http_post(url, payload, headers, backend.timeout_s)
        content = json.dumps(raw.get("data", raw))
        return InferenceResult(decision=decision, content=content, raw=raw, is_receipt=False)
