from __future__ import annotations

import os
from pathlib import Path
from typing import Protocol

import httpx

from .models import AnalysisRecord, MediaKind, PipelineInput


class Analyzer(Protocol):
    def analyze(self, pipeline_input: PipelineInput) -> AnalysisRecord:
        ...


class MockAnalyzer:
    def analyze(self, pipeline_input: PipelineInput) -> AnalysisRecord:
        name = pipeline_input.filename.lower()

        if "invoice" in name or pipeline_input.media_kind == MediaKind.DOCUMENT:
            return AnalysisRecord(
                analyzer_name="mock-content-understanding",
                analyzer_id="mock-document",
                labels=["invoice", "document", "finance"],
                summary="Detected a document-like asset and extracted basic finance fields.",
                confidence=0.91,
                raw_result={
                    "documentType": "invoice",
                    "fields": {
                        "invoiceNumber": "INV-1001",
                        "vendor": "Contoso",
                        "totalAmount": "1820.45",
                    },
                },
            )

        if pipeline_input.media_kind == MediaKind.IMAGE:
            return AnalysisRecord(
                analyzer_name="mock-content-understanding",
                analyzer_id="mock-image",
                labels=["inspection", "product"],
                summary="Detected an image suitable for inspection workflow.",
                confidence=0.88,
                raw_result={
                    "imageType": "inspection",
                    "objects": [{"label": "package", "confidence": 0.88}],
                },
            )

        if pipeline_input.media_kind == MediaKind.VIDEO:
            return AnalysisRecord(
                analyzer_name="mock-content-understanding",
                analyzer_id="mock-video",
                labels=["video", "surveillance", "incident"],
                summary="Detected a video requiring downstream review.",
                confidence=0.79,
                raw_result={
                    "videoType": "surveillance",
                    "events": [{"timestamp": "00:00:12", "label": "incident"}],
                },
            )

        return AnalysisRecord(
            analyzer_name="mock-content-understanding",
            analyzer_id="mock-generic",
            labels=["generic"],
            summary="No specialized route detected.",
            confidence=0.50,
            raw_result={"status": "generic"},
        )


class FoundryContentUnderstandingAnalyzer:
    def __init__(
        self,
        endpoint: str | None = None,
        analyzer_id: str | None = None,
        bearer_token: str | None = None,
        api_version: str = "2025-11-01",
        timeout_seconds: float = 60.0,
    ) -> None:
        self.endpoint = (endpoint or os.getenv("CONTENT_UNDERSTANDING_ENDPOINT", "")).rstrip("/")
        self.analyzer_id = analyzer_id or os.getenv("CONTENT_UNDERSTANDING_ANALYZER_ID", "")
        self.bearer_token = bearer_token or os.getenv("AZURE_AI_TOKEN", "")
        self.api_version = api_version
        self.timeout_seconds = timeout_seconds

    def analyze(self, pipeline_input: PipelineInput) -> AnalysisRecord:
        if not self.endpoint:
            raise ValueError("Missing CONTENT_UNDERSTANDING_ENDPOINT")
        if not self.analyzer_id:
            raise ValueError("Missing CONTENT_UNDERSTANDING_ANALYZER_ID")
        if not self.bearer_token:
            raise ValueError("Missing AZURE_AI_TOKEN")
        if not pipeline_input.source_uri.startswith(("http://", "https://")):
            raise ValueError(
                "Foundry analyzer requires a remote http(s) source_uri that the service can reach"
            )

        payload = {
            "inputs": [
                {
                    "url": pipeline_input.source_uri,
                }
            ]
        }

        url = (
            f"{self.endpoint}/contentunderstanding/analyzers/"
            f"{self.analyzer_id}:analyze?api-version={self.api_version}"
        )
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json",
        }

        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        labels = _extract_labels(data)
        summary = _extract_summary(data)

        return AnalysisRecord(
            analyzer_name="azure-content-understanding",
            analyzer_id=self.analyzer_id,
            labels=labels,
            summary=summary,
            confidence=None,
            raw_result=data,
        )


def infer_media_kind(filename: str, mime_type: str | None = None) -> MediaKind:
    mime = (mime_type or "").lower()
    suffix = Path(filename).suffix.lower()

    if mime.startswith("image/") or suffix in {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"}:
        return MediaKind.IMAGE
    if mime.startswith("video/") or suffix in {".mp4", ".mov", ".avi", ".mkv"}:
        return MediaKind.VIDEO
    if mime.startswith("audio/") or suffix in {".mp3", ".wav", ".m4a"}:
        return MediaKind.AUDIO
    if (
        mime.startswith("application/pdf")
        or suffix in {".pdf", ".docx", ".pptx", ".xlsx", ".txt"}
    ):
        return MediaKind.DOCUMENT
    return MediaKind.UNKNOWN


def _extract_labels(data: dict) -> list[str]:
    labels: list[str] = []
    for key in ("labels", "tags", "categories"):
        value = data.get(key)
        if isinstance(value, list):
            labels.extend(str(item).lower() for item in value)
    fields = data.get("fields")
    if isinstance(fields, dict):
        labels.extend(str(key).lower() for key in fields.keys())
    return sorted(set(labels)) or ["generic"]


def _extract_summary(data: dict) -> str | None:
    for key in ("summary", "description", "status"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None
