from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class MediaKind(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"
    AUDIO = "audio"
    UNKNOWN = "unknown"


class PipelineInput(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    source_uri: str
    filename: str
    mime_type: str
    media_kind: MediaKind
    customer_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    received_at_utc: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class AnalysisRecord(BaseModel):
    analyzer_name: str
    analyzer_id: str
    raw_result: Dict[str, Any]
    labels: List[str] = Field(default_factory=list)
    summary: Optional[str] = None
    confidence: Optional[float] = None


class RoutedOutput(BaseModel):
    route_key: str
    bucket: str
    normalized_type: str


class PipelineResult(BaseModel):
    request_id: str
    input: PipelineInput
    analysis: AnalysisRecord
    routed_output: RoutedOutput
    exported_files: Dict[str, str]


class BlobAssetCreatedEvent(BaseModel):
    event_type: str = "blob.created"
    source_uri: str
    filename: str
    mime_type: Optional[str] = None
    customer_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DeliveryRecord(BaseModel):
    destination: str
    status: str
    detail: Dict[str, Any] = Field(default_factory=dict)
