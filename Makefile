.PHONY: help test fmt tidy serve openapi

# Local Go build cache stays in repo to avoid permission issues.
GOCACHE ?= $(CURDIR)/.cache/go-build
GOMODCACHE ?= $(CURDIR)/.gomodcache

ifneq (,$(WORKLINE_GOCACHE))
GOCACHE := $(WORKLINE_GOCACHE)
endif
ifneq (,$(WORKLINE_GOMODCACHE))
GOMODCACHE := $(WORKLINE_GOMODCACHE)
endif

# Auto-load .env if present (not committed).
ifneq (,$(wildcard .env))
include .env
export $(shell sed -n 's/^\([^#][^=]*\)=.*/\1/p' .env)
endif

help:
	@echo "Available targets:"
	@echo "  test    - run go test ./... with local cache"
	@echo "  fmt     - gofmt Go sources"
	@echo "  tidy    - go mod tidy"
	@echo "  serve   - start API server (requires WORKLINE_JWT_SECRET)"

test:
	GOCACHE=$(GOCACHE) GOMODCACHE=$(GOMODCACHE) go test ./...

fmt:
	gofmt -w cmd internal sdk

tidy:
	GOCACHE=$(GOCACHE) GOMODCACHE=$(GOMODCACHE) go mod tidy

serve:
	@[ -n "$$WORKLINE_JWT_SECRET" ] || (echo "WORKLINE_JWT_SECRET is required" && exit 1)
	@[ -n "$$WORKLINE_DEFAULT_PROJECT" ] || (echo "WORKLINE_DEFAULT_PROJECT is required (set with 'wl project use <id>')" && exit 1)
	GOCACHE=$(GOCACHE) GOMODCACHE=$(GOMODCACHE) go run ./cmd/wl serve --addr 127.0.0.1:8080 --base-path /v0 --project "$$WORKLINE_DEFAULT_PROJECT"
