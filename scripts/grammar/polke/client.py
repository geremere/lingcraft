"""Thin HTTP client for the POLKE EGP annotation API."""

from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import quote

import httpx


class PolkeError(RuntimeError):
    """Raised when POLKE is unreachable or returns an error response."""


@dataclass(frozen=True)
class Annotation:
    construct_id: int
    begin: int
    end: int


class PolkeClient:
    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 60.0,
        verify_ssl: bool | None = None,
    ) -> None:
        self.base_url = (base_url or os.environ.get("POLKE_URL", "http://localhost")).rstrip("/")
        self.timeout = timeout
        if verify_ssl is None:
            verify_ssl = os.environ.get("POLKE_VERIFY_SSL", "true").lower() not in {
                "0",
                "false",
                "no",
            }
        self.verify_ssl = verify_ssl

    def annotate(self, text: str) -> list[Annotation]:
        if not text.strip():
            return []

        url = f"{self.base_url}/extractor?text={quote(text, safe='')}"
        try:
            response = httpx.post(url, timeout=self.timeout, verify=self.verify_ssl)
            response.raise_for_status()
        except httpx.ConnectError as exc:
            raise PolkeError(
                f"Cannot connect to POLKE at {self.base_url}. "
                "Start POLKE locally — see scripts/grammar/polke/README.md"
            ) from exc
        except httpx.HTTPError as exc:
            raise PolkeError(f"POLKE request failed: {exc}") from exc

        payload = response.json()
        message = payload.get("message") or ""
        if message:
            raise PolkeError(f"POLKE returned error: {message}")

        annotations: list[Annotation] = []
        for item in payload.get("annotationList", []):
            annotations.append(
                Annotation(
                    construct_id=int(item["constructID"]),
                    begin=int(item["begin"]),
                    end=int(item["end"]),
                )
            )
        return annotations

    def health_check(self) -> bool:
        try:
            self.annotate("I like coffee.")
            return True
        except PolkeError:
            return False


def annotate(text: str, base_url: str | None = None) -> list[Annotation]:
    return PolkeClient(base_url=base_url).annotate(text)


def construct_tag(construct_id: int) -> str:
    return f"egp-{construct_id}"
