"""One small client for any OpenAI-compatible chat API (Gemini by default).

Answers are cached on disk by a hash of everything sent, so re-running the
evaluation costs nothing until an instruction or an example changes.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path

import requests

DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"
DEFAULT_MODEL = "gemini-flash-lite-latest"
CACHE_DIR = Path(".cache")


class ModelError(RuntimeError):
    """The provider could not be reached or kept failing."""


@dataclass
class Reply:
    text: str
    model: str
    seconds: float
    input_tokens: int | None
    output_tokens: int | None
    cached: bool


class Client:
    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: int = 60,
        use_cache: bool = True,
    ) -> None:
        self.model = model or os.environ.get("AI_MODEL", DEFAULT_MODEL)
        self.base_url = (base_url or os.environ.get("AI_BASE_URL", DEFAULT_BASE_URL)).rstrip("/")
        self.api_key = api_key if api_key is not None else os.environ.get("AI_API_KEY", "")
        self.timeout = timeout
        self.use_cache = use_cache

    def chat(self, system: str, user: str, *, temperature: float = 0.0, max_tokens: int = 2000) -> Reply:
        body = {
            "model": self.model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        }
        key = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
        path = CACHE_DIR / f"{key}.json"
        if self.use_cache and path.exists():
            hit = json.loads(path.read_text(encoding="utf-8"))
            return Reply(
                hit["text"], self.model, hit["seconds"], hit.get("input_tokens"), hit.get("output_tokens"), cached=True
            )

        if not self.api_key:
            raise ModelError("Set AI_API_KEY (and optionally AI_BASE_URL, AI_MODEL) to run workflows.")

        started = time.perf_counter()
        last = ""
        for attempt in range(5):
            try:
                r = requests.post(
                    f"{self.base_url}/chat/completions",
                    json=body,
                    timeout=self.timeout,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
            except requests.RequestException as e:
                last = type(e).__name__
            else:
                if r.ok:
                    data = r.json()
                    text = (data.get("choices") or [{}])[0].get("message", {}).get("content") or ""
                    usage = data.get("usage") or {}
                    reply = Reply(
                        text,
                        self.model,
                        round(time.perf_counter() - started, 2),
                        usage.get("prompt_tokens"),
                        usage.get("completion_tokens"),
                        cached=False,
                    )
                    if self.use_cache:
                        CACHE_DIR.mkdir(exist_ok=True)
                        path.write_text(
                            json.dumps(
                                {
                                    "text": text,
                                    "seconds": reply.seconds,
                                    "input_tokens": reply.input_tokens,
                                    "output_tokens": reply.output_tokens,
                                }
                            ),
                            encoding="utf-8",
                        )
                    return reply
                last = f"HTTP {r.status_code}"
                if r.status_code not in (429, 500, 502, 503, 504):
                    break
            time.sleep(min(60, 4 * 2**attempt))  # free tiers rate-limit bursts: back off
        raise ModelError(f"The model call failed ({last}).")
