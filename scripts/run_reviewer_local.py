from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVIEW_SCRIPT = ROOT / "scripts" / "foundry_review.py"
DEFAULT_PROMPT = ROOT / "samples" / "reviewer-smoke.md"
DEFAULT_OUTPUT_DIR = ROOT / "output" / "local-review"
DEFAULT_ENV_FILE = ROOT / ".env.reviewer"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the local Foundry reviewer against a prompt"
    )
    parser.add_argument(
        "--prompt-file",
        default=str(DEFAULT_PROMPT),
        help="Prompt file to send to the reviewer",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory where outputs are written",
    )
    parser.add_argument(
        "--env-file",
        default=str(DEFAULT_ENV_FILE),
        help="Optional .env-style file that contains reviewer settings",
    )
    return parser.parse_args()


def required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing environment variable: {name}")
    return value


def optional_env(name: str) -> str:
    return os.getenv(name, "").strip()


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key and key not in os.environ:
            os.environ[key] = value


def build_command(prompt_file: Path, output_dir: Path) -> list[str]:
    endpoint = required_env("FOUNDRY_REVIEWER_ENDPOINT")
    model = required_env("FOUNDRY_REVIEWER_MODEL")
    api_key = optional_env("FOUNDRY_REVIEWER_API_KEY")
    bearer_token = optional_env("FOUNDRY_REVIEWER_BEARER_TOKEN")

    if not api_key and not bearer_token:
        raise ValueError(
            "Reviewer requires either FOUNDRY_REVIEWER_API_KEY or FOUNDRY_REVIEWER_BEARER_TOKEN"
        )

    text_file = output_dir / "reviewer-output.md"
    json_file = output_dir / "reviewer-raw.json"

    command = [
        sys.executable,
        str(REVIEW_SCRIPT),
        "--endpoint",
        endpoint,
        "--model",
        model,
        "--prompt-file",
        str(prompt_file),
        "--output-file",
        str(text_file),
        "--response-json-file",
        str(json_file),
    ]
    if api_key:
        command.extend(["--api-key", api_key])
    if bearer_token:
        command.extend(["--bearer-token", bearer_token])
    return command


def main() -> int:
    args = parse_args()
    prompt_file = Path(args.prompt_file).resolve()
    output_dir = Path(args.output_dir).resolve()
    env_file = Path(args.env_file).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    load_env_file(env_file)

    print("[run] reviewer")
    completed = subprocess.run(build_command(prompt_file, output_dir), check=False)
    if completed.returncode == 0:
        print(f"[ok] outputs written to {output_dir}")
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
