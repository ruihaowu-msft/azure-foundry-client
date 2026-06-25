from __future__ import annotations

from .models import AnalysisRecord, MediaKind, PipelineInput, RoutedOutput


def classify_output(pipeline_input: PipelineInput, analysis: AnalysisRecord) -> RoutedOutput:
    labels = {label.lower() for label in analysis.labels}
    media_kind = pipeline_input.media_kind

    if media_kind == MediaKind.DOCUMENT and {"invoice", "tax", "form"} & labels:
        return RoutedOutput(
            route_key="document-finance",
            bucket="finance-documents",
            normalized_type="financial_document",
        )

    if media_kind == MediaKind.IMAGE and {"damage", "inspection", "product"} & labels:
        return RoutedOutput(
            route_key="image-inspection",
            bucket="image-inspection",
            normalized_type="inspection_image",
        )

    if media_kind == MediaKind.VIDEO and {"incident", "safety", "surveillance"} & labels:
        return RoutedOutput(
            route_key="video-review",
            bucket="video-review",
            normalized_type="video_incident",
        )

    return RoutedOutput(
        route_key="manual-review",
        bucket="manual-review",
        normalized_type="unclassified",
    )
