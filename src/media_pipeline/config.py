from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    analyzer_mode: str = "mock"
    output_dir: str = "output"
    content_understanding_endpoint: str = ""
    content_understanding_analyzer_id: str = ""
    azure_ai_token: str = ""
    customer_callback_url: str = ""
    customer_callback_bearer_token: str = ""

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            analyzer_mode=os.getenv("PIPELINE_ANALYZER_MODE", "mock"),
            output_dir=os.getenv("PIPELINE_OUTPUT_DIR", "output"),
            content_understanding_endpoint=os.getenv("CONTENT_UNDERSTANDING_ENDPOINT", ""),
            content_understanding_analyzer_id=os.getenv(
                "CONTENT_UNDERSTANDING_ANALYZER_ID", ""
            ),
            azure_ai_token=os.getenv("AZURE_AI_TOKEN", ""),
            customer_callback_url=os.getenv("CUSTOMER_CALLBACK_URL", ""),
            customer_callback_bearer_token=os.getenv(
                "CUSTOMER_CALLBACK_BEARER_TOKEN", ""
            ),
        )
