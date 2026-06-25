from __future__ import annotations

from pathlib import Path
from typing import Any

from .analyzers import infer_media_kind
from .models import BlobAssetCreatedEvent, PipelineInput


def build_pipeline_input_from_blob_event(event: BlobAssetCreatedEvent) -> PipelineInput:
    mime_type = event.mime_type or guess_mime_from_name(event.filename)
    return PipelineInput(
        source_uri=event.source_uri,
        filename=event.filename,
        mime_type=mime_type,
        media_kind=infer_media_kind(event.filename, mime_type),
        customer_id=event.customer_id,
        metadata=event.metadata,
    )


def build_blob_event_from_dict(payload: dict[str, Any]) -> BlobAssetCreatedEvent:
    filename = payload.get("filename")
    source_uri = payload.get("source_uri")

    if not filename and source_uri:
        filename = Path(source_uri).name

    if not source_uri:
        raise ValueError("Blob event payload requires source_uri")
    if not filename:
        raise ValueError("Blob event payload requires filename")

    return BlobAssetCreatedEvent(
        source_uri=source_uri,
        filename=filename,
        mime_type=payload.get("mime_type"),
        customer_id=payload.get("customer_id"),
        metadata=payload.get("metadata", {}),
    )


def guess_mime_from_name(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    mapping = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".mp4": "video/mp4",
        ".mov": "video/quicktime",
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".txt": "text/plain",
    }
    return mapping.get(suffix, "application/octet-stream")
