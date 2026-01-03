Proofline CLI (`pl`)
====================

Proofline stores all state in SQLite at `.proofline/proofline.db` and requires a project configuration file at `.proofline/proofline.yml`.

Build / Install
---------------
- Requirements: Go 1.22+
- Build: `go build ./...`
- Optional caches for sandboxed environments: prefix commands with `GOMODCACHE=$(pwd)/.gomodcache GOCACHE=$(pwd)/.gocache`.

Initialization
--------------
- Run `pl init --project-id <id>` to create the workspace, database, and default config.
- Default config (editable) is generated with:
  - Attestation catalog entries for `ci.passed`, `review.approved`, `acceptance.passed`, `security.ok`, `iteration.approved`.
  - Policy presets: `low`, `medium`, `high`, `feature`, `bug`, `technical` as defined in the generated YAML.
  - Task defaults mapping task types to presets, and iteration validation requiring `iteration.approved`.
- `pl init` records events `project.init` and `config.created`.

Configuration
-------------
- `.proofline/proofline.yml` is the single source of truth for validation policies and attestation catalog.
- All commands load and validate this file; commands fail if it is missing or invalid (except `pl init` which creates it).
- Validate config: `pl config validate` (or inspect with `pl config show` / `--json`).
- Default policies are applied automatically on task creation based on `policies.defaults.task.<type>` unless overridden with `--policy` or explicit validation flags (`--validation-mode`, `--require`, `--threshold`), which emit `policy.override`.
- Iteration validation uses `policies.defaults.iteration.validation.require`; missing value means no attestation is required.

Quick Start
-----------
```sh
pl init --project-id myproj --description "Demo project"
pl config show
pl iteration create --id iter-1 --goal "Ship MVP"
pl task create --type feature --title "Implement auth"
pl task list
pl task claim <task-id>
pl task update <task-id> --status in_progress
pl attest add --entity-kind task --entity-id <task-id> --kind ci.passed
pl task done <task-id> --work-proof-json '{"notes":"implemented and tested"}'
pl log tail
```

Common Commands
---------------
- Status: `pl status`
- Tasks:
  - Create with policy preset: `pl task create --type feature --title "..." --policy high`
  - Update with preset: `pl task update <id> --set-policy medium`
  - Tree view: `pl task tree`
- Iterations:
  - Set status: `pl iteration set-status <id> --status validated`
- Attestations:
  - Add: `pl attest add --entity-kind iteration --entity-id iter-1 --kind iteration.approved`
  - List: `pl attest list --entity-kind task --entity-id <id>`
- Logs: `pl log tail --n 50`

Events and Policies
-------------------
- All state changes append to `events` (SQLite). Policy-related events include `task.policy.applied`, `task.policy.updated`, `policy.override`, and `iteration.validation.checked`.
- Validation decisions use the policy fields persisted on each task; presets from config populate these fields on create or when `--set-policy` is used.

Testing
-------
Run `go test ./...` (use `GOMODCACHE`/`GOCACHE` env vars if needed for sandboxed environments).

Contributing
------------
See `CONTRIBUTING.md` for coding standards, testing expectations, and PR checklist.
