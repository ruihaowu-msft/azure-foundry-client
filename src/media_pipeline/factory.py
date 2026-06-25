from __future__ import annotations

from .analyzers import FoundryContentUnderstandingAnalyzer, MockAnalyzer
from .config import AppConfig
from .delivery import (
    HttpCallbackPublisher,
    LocalCallbackCapturePublisher,
    NullPublisher,
    ResultPublisher,
)
from .pipeline import PipelineRunner
from .storage import LocalJsonStore


def build_pipeline_runner(config: AppConfig) -> PipelineRunner:
    analyzer = (
        MockAnalyzer()
        if config.analyzer_mode == "mock"
        else FoundryContentUnderstandingAnalyzer(
            endpoint=config.content_understanding_endpoint,
            analyzer_id=config.content_understanding_analyzer_id,
            bearer_token=config.azure_ai_token,
        )
    )

    return PipelineRunner(
        analyzer=analyzer,
        store=LocalJsonStore(config.output_dir),
        publisher=build_result_publisher(config),
    )


def build_result_publisher(config: AppConfig) -> ResultPublisher:
    if config.customer_callback_url:
        return HttpCallbackPublisher(
            callback_url=config.customer_callback_url,
            bearer_token=config.customer_callback_bearer_token,
        )
    if config.output_dir:
        return LocalCallbackCapturePublisher(config.output_dir)
    return NullPublisher()
