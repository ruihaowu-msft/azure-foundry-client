from __future__ import annotations

import argparse
import json
import socket
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a review prompt against an Azure Foundry model")
    parser.add_argument("--endpoint", required=True, help="Azure OpenAI / Foundry endpoint root")
    parser.add_argument("--model", required=True, help="Deployment or model name")
    parser.add_argument("--prompt-file", required=True, help="Path to the full prompt markdown")
    parser.add_argument("--output-file", required=True, help="Where to write the model text output")
    parser.add_argument(
        "--api-key",
        default="",
        help="API key for the Foundry deployment. Optional when bearer token is used.",
    )
    parser.add_argument(
        "--bearer-token",
        default="",
        help="Bearer token for the Foundry deployment. Optional when api-key is used.",
    )
    parser.add_argument(
        "--response-json-file",
        default="",
        help="Optional path to save the raw JSON response for debugging",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=300,
        help="HTTP timeout for each reviewer request attempt",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=1,
        help="How many times to retry transient network failures after the first attempt",
    )
    parser.add_argument(
        "--retry-delay-seconds",
        type=int,
        default=5,
        help="Delay between retry attempts for transient network failures",
    )
    return parser.parse_args()


def normalize_endpoint(endpoint: str) -> str:
    value = endpoint.rstrip("/")
    if value.endswith("/openai/v1"):
        return value
    if value.endswith("/openai"):
        return f"{value}/v1"
    return f"{value}/openai/v1"


def extract_output_text(payload: dict) -> str:
    output_text = payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    collected: list[str] = []
    for item in payload.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if not isinstance(content, dict):
                continue
            text = content.get("text")
            if isinstance(text, str) and text.strip():
                collected.append(text.strip())

    if collected:
        return "\n\n".join(collected)

    return json.dumps(payload, ensure_ascii=False, indent=2)


def read_response(
    request: urllib.request.Request,
    *,
    timeout_seconds: int,
    max_retries: int,
    retry_delay_seconds: int,
) -> str:
    attempts = max_retries + 1
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                return response.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Foundry request failed with HTTP {error.code}: {detail}"
            ) from error
        except (TimeoutError, socket.timeout, urllib.error.URLError) as error:
            last_error = error
            if attempt >= attempts:
                break
            sys.stderr.write(
                f"[warn] Foundry request attempt {attempt}/{attempts} failed: {error}. "
                f"Retrying in {retry_delay_seconds}s.\n"
            )
            time.sleep(retry_delay_seconds)

    raise RuntimeError(
        f"Foundry request failed after {attempts} attempt(s): {last_error}"
    ) from last_error


def main() -> int:
    args = parse_args()
    if not args.api_key and not args.bearer_token:
        raise ValueError("Either --api-key or --bearer-token must be provided")

    prompt = Path(args.prompt_file).read_text(encoding="utf-8")
    url = f"{normalize_endpoint(args.endpoint)}/responses"

    payload = {
        "model": args.model,
        "input": prompt,
    }
    body = json.dumps(payload).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "foundry-media-pipeline-prototype-reviewer",
    }
    if args.api_key:
        headers["api-key"] = args.api_key
    if args.bearer_token:
        headers["Authorization"] = f"Bearer {args.bearer_token}"

    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    raw = read_response(
        request,
        timeout_seconds=args.timeout_seconds,
        max_retries=args.max_retries,
        retry_delay_seconds=args.retry_delay_seconds,
    )

    data = json.loads(raw)
    if args.response_json_file:
        Path(args.response_json_file).write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    text = extract_output_text(data)
    Path(args.output_file).write_text(text + "\n", encoding="utf-8")
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
