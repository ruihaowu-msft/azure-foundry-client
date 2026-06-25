# Foundry Reviewer Setup

This repository supports a report-only reviewer flow backed by an Azure AI Foundry model.

## What this automation does

- runs on pull requests
- sends the PR diff and review instructions to a Foundry reviewer model
- posts or updates one PR comment with the review result
- posts or updates one PR comment when the reviewer workflow fails
- can send a Teams webhook alert when findings are present
- can send a Teams webhook alert when the reviewer workflow fails
- does not change code automatically

## Repository configuration

Set these repository variables:

- `FOUNDRY_REVIEWER_ENDPOINT`
- `FOUNDRY_REVIEWER_MODEL`

Set one of these repository secrets:

- `FOUNDRY_REVIEWER_API_KEY`
- `FOUNDRY_REVIEWER_BEARER_TOKEN`

Optional repository secret:

- `TEAMS_ALERT_WEBHOOK_URL`

## Teams pop-up alerts

Recommended setup:

1. In Microsoft Teams, create a Workflow that starts with `When a Teams webhook request is received`.
2. Have that workflow post a message or Adaptive Card into a chat or channel you actually watch.
3. Copy the generated webhook URL.
4. Save it in the repository secret `TEAMS_ALERT_WEBHOOK_URL`.

The GitHub workflow sends two alert types:

- `review_findings`: the reviewer finished and found issues
- `review_failure`: the reviewer workflow itself failed before it could produce a complete report

## Local smoke test

Create a local `.env.reviewer` file from `.env.reviewer.example`, then run:

```bash
cd /Users/williamwu/scratch/foundry-media-pipeline-prototype
python3 scripts/run_reviewer_local.py
```

The local script writes outputs under `output/local-review/`.

## Files

- `.github/workflows/foundry-review.yml`
- `.github/prompts/foundry-review.md`
- `AGENTS.md`
- `scripts/foundry_review.py`
- `scripts/run_reviewer_local.py`
