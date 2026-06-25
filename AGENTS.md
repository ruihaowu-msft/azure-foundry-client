# AGENTS.md

This repository uses a report-first Foundry reviewer workflow.

## Roles

- The execution model stays outside this repository in the user's Codex setup.
- The reviewer model is a separate Azure AI Foundry deployment.
- Automated checks only report findings.
- A human decides whether any follow-up code change should happen.

## Working rules

- Automated review must not change repository files or push fixes.
- Prefer narrow, reviewable patches over broad refactors.
- Keep reviewer auth assumptions explicit. Reviewer auth may use API key or Entra / bearer-token flows depending on deployment constraints.
- Treat Azure connectivity as environment-specific. Local scripts should fail clearly when auth or network is unavailable.

## Review standard

Reviewers should prioritize:

1. Bugs and behavioral regressions
2. Security and permission risks
3. Schema / contract drift
4. Missing tests
5. Maintainability issues that create delivery risk

## Local verification

Run these commands after meaningful reviewer automation changes:

```bash
cd /Users/williamwu/scratch/foundry-media-pipeline-prototype
python3 scripts/run_reviewer_local.py
python3 scripts/foundry_review.py \
  --endpoint "https://your-resource.openai.azure.com" \
  --model "gpt-5.4-pro" \
  --prompt-file samples/reviewer-smoke.md \
  --output-file /tmp/reviewer-smoke-out.md \
  --api-key "your-key"
```

## Pull request review output shape

Review comments should be concise and actionable. Prefer this structure:

- Severity
- File or component
- Why it matters
- Suggested fix
