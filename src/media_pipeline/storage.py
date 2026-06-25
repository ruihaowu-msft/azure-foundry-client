from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from .models import PipelineResult


class LocalJsonStore:
    def __init__(self, base_dir: str | Path) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def export(self, result: PipelineResult) -> Dict[str, str]:
        route_dir = self.base_dir / result.routed_output.bucket / result.request_id
        route_dir.mkdir(parents=True, exist_ok=True)

        raw_path = route_dir / "raw-analysis.json"
        normalized_path = route_dir / "normalized-output.json"

        raw_path.write_text(
            json.dumps(result.analysis.raw_result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        normalized_path.write_text(
            json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return {
            "raw_analysis": str(raw_path),
            "normalized_output": str(normalized_path),
        }
