from __future__ import annotations

import argparse
import json
from pathlib import Path

from .analyzers import infer_media_kind
from .config import AppConfig
from .factory import build_pipeline_runner
from .function_app import process_blob_created_event
from .ingestion import guess_mime_from_name
from .models import PipelineInput


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Foundry media pipeline prototype")
    subparsers = parser.add_subparsers(dest="command", required=True)

    process_parser = subparsers.add_parser("process", help="Process a single asset")
    process_parser.add_argument("--file", required=True, help="Local file path for metadata")
    process_parser.add_argument(
        "--source-uri",
        help="Public or pre-signed URI. Defaults to file:// URI for local dry runs.",
    )
    process_parser.add_argument("--mime-type", default="", help="Optional mime type override")
    process_parser.add_argument(
        "--mode",
        choices=["mock", "foundry"],
        default="mock",
        help="Analyzer mode",
    )
    process_parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory where normalized results are written",
    )
    process_parser.add_argument("--customer-id", default=None)

    event_parser = subparsers.add_parser(
        "process-event",
        help="Process a blob-created style event payload",
    )
    event_parser.add_argument("--event-file", required=True, help="Path to event json file")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "process":
        return _process_single_asset(args)
    if args.command == "process-event":
        return _process_blob_event(args)
    raise ValueError(f"Unsupported command: {args.command}")


def _process_single_asset(args: argparse.Namespace) -> int:
    file_path = Path(args.file).resolve()
    mime_type = args.mime_type or guess_mime_from_name(file_path.name)
    source_uri = args.source_uri or file_path.as_uri()

    pipeline_input = PipelineInput(
        source_uri=source_uri,
        filename=file_path.name,
        mime_type=mime_type,
        media_kind=infer_media_kind(file_path.name, mime_type),
        customer_id=args.customer_id,
        metadata={"local_path": str(file_path)},
    )

    current = AppConfig.from_env()
    config = AppConfig(
        analyzer_mode=args.mode,
        output_dir=args.output_dir,
        content_understanding_endpoint=current.content_understanding_endpoint,
        content_understanding_analyzer_id=current.content_understanding_analyzer_id,
        azure_ai_token=current.azure_ai_token,
        customer_callback_url=current.customer_callback_url,
        customer_callback_bearer_token=current.customer_callback_bearer_token,
    )
    runner = build_pipeline_runner(config)
    result, delivery = runner.run(pipeline_input)
    print(
        json.dumps(
            {
                "result": result.model_dump(mode="json"),
                "delivery": delivery.model_dump(mode="json"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def _process_blob_event(args: argparse.Namespace) -> int:
    event_file = Path(args.event_file).resolve()
    payload = json.loads(event_file.read_text(encoding="utf-8"))
    print(json.dumps(process_blob_created_event(payload), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
