from __future__ import annotations

import json
from typing import Any

from .config import AppConfig
from .factory import build_pipeline_runner
from .ingestion import build_blob_event_from_dict, build_pipeline_input_from_blob_event


def process_blob_created_event(
    payload: dict[str, Any],
    config: AppConfig | None = None,
) -> dict[str, Any]:
    app_config = config or AppConfig.from_env()
    event = build_blob_event_from_dict(payload)
    pipeline_input = build_pipeline_input_from_blob_event(event)
    runner = build_pipeline_runner(app_config)
    result, delivery = runner.run(pipeline_input)
    return {
        "result": result.model_dump(mode="json"),
        "delivery": delivery.model_dump(mode="json"),
    }


def main(raw_payload: str) -> str:
    payload = json.loads(raw_payload)
    output = process_blob_created_event(payload)
    return json.dumps(output, ensure_ascii=False, indent=2)
