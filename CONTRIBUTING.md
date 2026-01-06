# Contributing to Workline

Thank you for improving Workline. Please follow these guidelines to keep the project stable and consistent.

## Getting Started
- Go version: 1.22+
- Install dependencies via `go mod tidy` (use `WORKLINE_GOMODCACHE`/`WORKLINE_GOCACHE` env vars if needed in sandboxed environments).
- Workspace layout lives under `.workline/` (database only); never check this directory into git.

## Coding Standards
- Keep all business logic in the engine layer; repositories must stay query-only.
- Policies and attestations come solely from the project config in the DB; import via `wl project config import --file <path>` and do not hardcode policy data in code.
- Maintain strict status transition and validation rules enforced in the engine.
- Write clear, minimal comments only where logic is non-obvious; prefer readable code.

## Testing
- Add or update tests when changing behavior. Required suite:
  - `go test ./...`
- Ensure migrations and embedded assets remain in sync.

## CLI Expectations
- All commands must load and validate the project config.
- Preserve JSON output compatibility (`--json`) for machine consumers.

## Pull Request Checklist
- `gofmt` all touched Go files.
- `go test ./...` passes.
- No committed artifacts from `.workline/`, build outputs, or editor temp files.
