# CI/CD Quality Gate

Finplex AI is a local-first product, so the project does not deploy to a cloud service. In this repository, CI/CD means continuous integration plus delivery readiness: every pull request must prove that the product can still be linted, tested, built, and evaluated before it is merged into `main`.

## GitHub Actions

The workflow lives in:

```text
.github/workflows/ci.yml
```

It runs on every pull request and every push to `main`.

## CI Stages

| Stage | Command | Purpose |
|---|---|---|
| Secret scan | `bash scripts/check-secrets.sh` | Blocks obvious committed secrets and secret files |
| Python lint | `bash scripts/lint.sh` | Runs Ruff over backend, services, admin, scripts, evals, and tests |
| React build | `bash scripts/lint.sh` | Runs the TypeScript/Vite production build |
| Unit tests | `bash scripts/test.sh` | Runs API, model-server, guardrails, worker, and admin import checks |
| Golden evals | `bash scripts/run-evals.sh` | Runs extraction, RAG, risk, policy, and end-to-end evaluation gates |

## Local Commands

Run the same quality gate locally before opening or merging a PR:

```bash
bash scripts/check-secrets.sh
bash scripts/lint.sh
bash scripts/test.sh
bash scripts/run-evals.sh
```

For a full local product check with data:

```bash
make infra-up
bash scripts/seed-local-data.sh --reset-product-tenants
bash scripts/check-secrets.sh
bash scripts/lint.sh
bash scripts/test.sh
bash scripts/run-evals.sh
```

## Why Evals Are Part Of CI

Normal unit tests confirm code behavior. Evals confirm product behavior:

- invoice extraction still recognizes key fields
- RAG still retrieves the right supporting evidence
- risk scoring remains consistent for known cases
- policy checks still block unsafe or unsupported drafts
- the offline AI quality gate passes end to end

The thresholds are intentionally stored in:

```text
evals/eval_thresholds.yaml
```

This makes quality expectations visible and reviewable.

## Reports

Every eval writes a JSON report under:

```text
reports/evals/
```

Reports are generated artifacts and should not be committed.
