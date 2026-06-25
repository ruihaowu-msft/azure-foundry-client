# AGENTS.md

This project uses a report-first review workflow.

## Roles

- Reviewer A is a model deployed in Azure AI Foundry.
- Reviewer B is a second model deployed in Azure AI Foundry.
- Automated checks only report findings.
- The human owner decides whether any code should be changed after the report.

## Working rules

- Automated review must not change repository files or push fixes.
- Prefer narrow, reviewable patches over broad refactors.
- Preserve the current prototype structure unless a change is required for the task.
- Keep auth assumptions explicit. This project may use Azure OpenAI API keys or Entra / bearer-token style flows depending on deployment constraints.
- Treat network-dependent Azure validation as environment-specific. Keep local mock paths working even when Azure access is unavailable.

## Review standard

Reviewers should prioritize:

1. Bugs and behavioral regressions
2. Security and permission risks
3. Schema / contract drift
4. Missing tests
5. Maintainability issues that create real delivery risk

## Local verification

Run these commands after meaningful changes:

```bash
cd /Users/williamwu/scratch/foundry-media-pipeline-prototype
.venv/bin/pytest -q
.venv/bin/python -m media_pipeline.cli process --file samples/invoice-sample.pdf --mode mock
.venv/bin/python -m media_pipeline.cli process-event --event-file samples/blob-event.json
```

## Pull request review output shape

Review comments should be concise and actionable. Prefer this structure:

- Severity
- File or component
- Why it matters
- Suggested fix
