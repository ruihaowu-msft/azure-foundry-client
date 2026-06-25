from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send a reviewer alert to an HTTP webhook")
    parser.add_argument("--webhook-url", required=True, help="Destination webhook URL")
    parser.add_argument("--status", required=True, help="Alert type, for example review_findings or review_failure")
    parser.add_argument("--repo", required=True, help="Repository name, such as owner/name")
    parser.add_argument("--pr-number", required=True, help="Pull request number")
    parser.add_argument("--pr-title", required=True, help="Pull request title")
    parser.add_argument("--pr-url", required=True, help="Pull request URL")
    parser.add_argument("--run-url", required=True, help="GitHub Actions run URL")
    parser.add_argument("--commit", required=True, help="Commit SHA")
    parser.add_argument("--failed-steps", default="", help="Comma-separated failed step names")
    parser.add_argument(
        "--details-file",
        default="",
        help="Optional text file whose contents will be included in the payload",
    )
    return parser.parse_args()


def read_details(path: str) -> str:
    if not path:
        return ""
    file_path = Path(path)
    if not file_path.exists():
        return ""
    text = file_path.read_text(encoding="utf-8").strip()
    if len(text) > 4000:
        return text[:4000] + "\n\n[truncated]"
    return text


def main() -> int:
    args = parse_args()
    payload = {
        "status": args.status,
        "repository": args.repo,
        "pullRequestNumber": args.pr_number,
        "pullRequestTitle": args.pr_title,
        "pullRequestUrl": args.pr_url,
        "runUrl": args.run_url,
        "commit": args.commit[:7],
    }
    if args.failed_steps:
        payload["failedSteps"] = [step.strip() for step in args.failed_steps.split(",") if step.strip()]

    details = read_details(args.details_file)
    if details:
        payload["details"] = details

    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        args.webhook_url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        response.read()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
