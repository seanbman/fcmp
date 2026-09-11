#!/usr/bin/env python3
"""Development-branch Grapher entrypoint for Neith.

Extends the canonical full-repository indexer with semantic summaries for
framework-planning and implementation artifacts that exist on dev before
invoking the normal index/validate/audit/publish pipeline.
"""

import index_grapher as base

base.SUMMARIES.update({
    "docs/DEVELOPMENT_PLAN_0926-1.md": (
        "Neith pre-1.0 framework development plan 0926-1. It converts the 2026-09-10 "
        "architecture and developer-experience strategy into staged implementation work: "
        "first-class Application ownership, state semantics, deterministic events, a secure "
        "versioned Go/browser protocol, a tiny trusted browser instruction interpreter, "
        "WebSocket/session/upload hardening, API simplification, ADRs, CI gates, documentation, "
        "Grapher governance, examples, observability, and release discipline."
    ),
    "docs/API_SURFACE_0926-1.md": (
        "Pre-1.0 API migration inventory classifying Neith concepts as canonical, compatibility, "
        "advanced, or candidate-internal. It prevents temporary implementation vocabulary from "
        "becoming accidental 1.0 commitments and records migration rules and invariants."
    ),
    "docs/adr/0001-framework-thesis.md": (
        "Accepted architecture decision establishing the Neith thesis: ordinary Go owns application "
        "behavior and rendering while Neith supplies interactivity through a thin browser runtime, "
        "remaining renderer-neutral and compatible with net/http."
    ),
    "docs/adr/0002-application-runtime-ownership.md": (
        "Accepted architecture decision making Application the canonical owner of configuration, "
        "runtime, routes, lifecycle, sessions and future policy; routes within an Application share "
        "one deliberate runtime while separate Applications remain isolated."
    ),
    "docs/adr/0003-protocol-security-boundary.md": (
        "Accepted security/architecture decision defining the browser as a finite versioned protocol "
        "interpreter and explicitly rejecting arbitrary server-supplied JavaScript execution."
    ),
    "application.go": (
        "Introduces the first-class Application API for framework plan 0926-1. Application owns an "
        "isolated runtime and standard-library ServeMux, implements http.Handler, registers multiple "
        "interactive routes against the shared runtime, serves embedded assets, and accepts local "
        "configuration options without requiring package-global configuration."
    ),
    "application_test.go": (
        "Phase 1 contract tests for Application: registered HTTP route/page serving, multiple routes "
        "sharing one application runtime, isolation between separate applications, and proof that "
        "application-local configuration does not mutate the legacy package-global configuration."
    ),
    "handler.go": (
        "Runtime handler pool and bidirectional dispatch pipeline. Legacy MiddleWareFn preserves a "
        "fresh isolated runtime per mount, while middleWareFnWithRuntime is the internal bridge that "
        "lets first-class Application routes share one deliberate runtime boundary."
    ),
    "pkg.go": (
        "Neith configuration definitions and legacy global compatibility path. Local configuration "
        "normalization is separated from SetConfig so first-class Application construction can own "
        "configuration without mutating process-global Neith state."
    ),
    "AGENTS.md": (
        "Repository operating guidance aligned with plan 0926-1. It requires agents to read the "
        "active plan, ADRs and API classification, use Grapher continuously, preserve Application "
        "runtime isolation and finite-browser-protocol invariants, and keep tests/docs/generated "
        "assets synchronized."
    ),
    "scripts/index_grapher_dev.py": (
        "Development-branch Grapher entrypoint that augments the canonical repository indexer's "
        "semantic summary map for dev-only framework planning and implementation artifacts, then "
        "delegates to the same full ingest, enrichment, validation, audit, search, and publish pipeline."
    ),
    ".github/workflows/grapher-index.yml": (
        "GitHub Actions workflow that keeps the dev branch semantically indexed with the canonical "
        "seanbman/grapher CLI, executes the dev Grapher entrypoint, validates and publishes the "
        "shared graph, and commits generated .grapher/shared state back with a recursion guard."
    ),
    "docs/README.md": (
        "Documentation index and mental-model entrypoint for Neith. It links the active 0926-1 "
        "framework plan with architecture, usage, browser, development, and repository references; "
        "states the server-driven Go mental model; and explains Grapher/source-of-truth policy."
    ),
})

if __name__ == "__main__":
    base.main()
