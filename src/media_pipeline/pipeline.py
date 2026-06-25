from __future__ import annotations

from .analyzers import Analyzer
from .classifier import classify_output
from .delivery import NullPublisher, ResultPublisher
from .models import DeliveryRecord, PipelineInput, PipelineResult
from .storage import LocalJsonStore


class PipelineRunner:
    def __init__(
        self,
        analyzer: Analyzer,
        store: LocalJsonStore,
        publisher: ResultPublisher | None = None,
    ) -> None:
        self.analyzer = analyzer
        self.store = store
        self.publisher = publisher or NullPublisher()

    def run(self, pipeline_input: PipelineInput) -> tuple[PipelineResult, DeliveryRecord]:
        analysis = self.analyzer.analyze(pipeline_input)
        routed_output = classify_output(pipeline_input, analysis)

        result = PipelineResult(
            request_id=pipeline_input.request_id,
            input=pipeline_input,
            analysis=analysis,
            routed_output=routed_output,
            exported_files={},
        )
        result.exported_files = self.store.export(result)
        delivery = self.publisher.publish(result)
        return result, delivery
