#!/usr/bin/env bash
set -euo pipefail

WORKLINE_WORKSPACE="${WORKLINE_WORKSPACE:-.}"
WORKLINE_GOCACHE="${WORKLINE_GOCACHE:-${WORKLINE_WORKSPACE}/.cache/go-build}"

echo "==> Workspace: ${WORKLINE_WORKSPACE}"
echo "==> Go cache: ${WORKLINE_GOCACHE}"

echo "==> Downloading Go modules"
GOCACHE="${WORKLINE_GOCACHE}" go mod download

if [ -n "${WORKLINE_DEFAULT_PROJECT_CONFIG_FILE:-}" ]; then
  echo "==> Importing config into DB: ${WORKLINE_DEFAULT_PROJECT_CONFIG_FILE}"
  GOCACHE="${WORKLINE_GOCACHE}" go run ./cmd/wl project config import --file "${WORKLINE_DEFAULT_PROJECT_CONFIG_FILE}" --workspace "${WORKLINE_WORKSPACE}"
fi

echo "Done. DB will be created on first command if missing at ${WORKLINE_WORKSPACE}/.workline/workline.db"
