#!/usr/bin/env python3
"""Development-branch Grapher entrypoint for Neith.

Extends the canonical full-repository indexer with semantic summaries for
framework-planning artifacts that exist on dev before invoking the normal
index/validate/audit/publish pipeline.
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
    "scripts/index_grapher_dev.py": (
        "Development-branch Grapher entrypoint that augments the canonical repository indexer's "
        "semantic summary map for dev-only framework planning artifacts, then delegates to the "
        "same full ingest, enrichment, validation, audit, search, and publish pipeline."
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
