from __future__ import annotations

from pathlib import Path
from typing import Protocol

import httpx

from .models import DeliveryRecord, PipelineResult


class ResultPublisher(Protocol):
    def publish(self, result: PipelineResult) -> DeliveryRecord:
        ...


class NullPublisher:
    def publish(self, result: PipelineResult) -> DeliveryRecord:
        return DeliveryRecord(
            destination="none",
            status="skipped",
            detail={"reason": "No downstream callback configured"},
        )


class LocalCallbackCapturePublisher:
    def __init__(self, base_dir: str | Path) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def publish(self, result: PipelineResult) -> DeliveryRecord:
        path = self.base_dir / result.request_id / "callback-payload.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        return DeliveryRecord(
            destination="local-callback-capture",
            status="captured",
            detail={"path": str(path)},
        )


class HttpCallbackPublisher:
    def __init__(
        self,
        callback_url: str,
        bearer_token: str = "",
        timeout_seconds: float = 30.0,
    ) -> None:
        self.callback_url = callback_url
        self.bearer_token = bearer_token
        self.timeout_seconds = timeout_seconds

    def publish(self, result: PipelineResult) -> DeliveryRecord:
        headers = {"Content-Type": "application/json"}
        if self.bearer_token:
            headers["Authorization"] = f"Bearer {self.bearer_token}"

        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(
                self.callback_url,
                headers=headers,
                content=result.model_dump_json(),
            )
            response.raise_for_status()

        return DeliveryRecord(
            destination=self.callback_url,
            status="sent",
            detail={"status_code": response.status_code},
        )
