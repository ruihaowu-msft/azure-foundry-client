# Foundry Reviewer Setup

This repository supports a report-only reviewer flow backed by an Azure AI Foundry model.

## What this automation does

- runs on pull requests
- sends the PR diff and review instructions to a Foundry reviewer model
- posts or updates one PR comment with the review result
- posts or updates one PR comment when the reviewer workflow fails
- does not change code automatically
- works well with ordinary GitHub email notifications for PR comments and Actions failures

## Repository configuration

Set these repository variables:

- `FOUNDRY_REVIEWER_ENDPOINT`
- `FOUNDRY_REVIEWER_MODEL`

Set one of these repository secrets:

- `FOUNDRY_REVIEWER_API_KEY`
- `FOUNDRY_REVIEWER_BEARER_TOKEN`

## Notifications

Recommended setup:

1. Keep the reviewer PR comments enabled through the workflow in this repository.
2. Turn on GitHub email notifications for pull request comments and GitHub Actions updates on your account.
3. Watch the repository or at least keep notifications enabled for pull requests you open or participate in.

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
