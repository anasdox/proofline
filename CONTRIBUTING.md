# Contributing to Proofline

Thank you for improving Proofline. Please follow these guidelines to keep the project stable and consistent.

## Getting Started
- Go version: 1.22+
- Install dependencies via `go mod tidy` (use `GOMODCACHE`/`GOCACHE` env vars if needed in sandboxed environments).
- Workspace layout lives under `.proofline/` (database + config); never check this directory into git.

## Coding Standards
- Keep all business logic in the engine layer; repositories must stay query-only.
- Policies and attestations come solely from `.proofline/proofline.yml`—do not hardcode policy data in code.
- Maintain strict status transition and validation rules enforced in the engine.
- Write clear, minimal comments only where logic is non-obvious; prefer readable code.

## Testing
- Add or update tests when changing behavior. Required suite:
  - `go test ./...`
- Ensure migrations and embedded assets remain in sync.

## CLI Expectations
- All commands must load and validate the project config (except `pl init`, which creates it).
- Preserve JSON output compatibility (`--json`) for machine consumers.

## Pull Request Checklist
- `gofmt` all touched Go files.
- `go test ./...` passes.
- No committed artifacts from `.proofline/`, build outputs, or editor temp files.
