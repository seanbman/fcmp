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
        "Accepted and Phase-1-implemented architecture decision making Application the canonical "
        "owner of configuration, runtime, routes, lifecycle, sessions and future policy. Routes "
        "within an Application share one deliberate runtime; separate Applications remain isolated; "
        "shutdown cancels runtime work, closes tracked sockets, rejects new requests, and is idempotent."
    ),
    "docs/adr/0003-protocol-security-boundary.md": (
        "Accepted security/architecture decision defining the browser as a finite versioned protocol "
        "interpreter and explicitly rejecting arbitrary server-supplied JavaScript execution."
    ),
    "application.go": (
        "First-class Application API for framework plan 0926-1. Application owns an isolated runtime "
        "and standard-library ServeMux, implements http.Handler, registers multiple interactive routes "
        "against one shared runtime, serves embedded assets, accepts local configuration without "
        "package globals, and exposes Done, Shutdown, and Close lifecycle methods."
    ),
    "application_test.go": (
        "Phase 1 contract tests for Application: registered HTTP route/page serving, multiple routes "
        "sharing one application runtime, isolation between separate applications, application-local "
        "configuration, idempotent shutdown, post-shutdown request rejection, and closure/detachment "
        "of tracked active connections."
    ),
    "runtime.go": (
        "Internal Application runtime ownership boundary. In addition to handlers, sessions, listeners, "
        "state stores and configuration, runtime now owns a cancellation context, closed state, tracked "
        "connection wait group, and idempotent graceful shutdown that closes active session sockets."
    ),
    "handler.go": (
        "Runtime handler pool and bidirectional dispatch pipeline. Legacy MiddleWareFn preserves a "
        "fresh isolated runtime per mount; middleWareFnWithRuntime lets Application routes share one "
        "runtime. Handler input/output loops, ping loops, initial dispatch, and event responses now "
        "observe runtime cancellation so application shutdown terminates runtime-owned pipelines."
    ),
    "conn.go": (
        "WebSocket transport tied to Application runtime lifetime. Connections are registered with the "
        "runtime after upgrade, close exactly once, decrement runtime tracking, stop reads/writes and "
        "publishes on runtime cancellation, skip delayed cache cleanup during shutdown, and continue "
        "to enforce one active connection per client session."
    ),
    "session.go": (
        "Client-session registry preserving one active socket per browser client while allowing session "
        "state to outlive a connection. It now exposes an internal snapshot of active connections so "
        "Application shutdown can close every transport owned by the runtime safely."
    ),
    "errors.go": (
        "Stable package error values for application lifecycle, dispatch/event context, connection "
        "failures, and cache/store failures. ErrApplicationClosed identifies work rejected after an "
        "Application runtime has begun shutdown."
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
        "GitHub Actions workflow for dev verification. It runs the Go test suite before installing "
        "canonical seanbman/grapher, builds and audits the semantic repository index, publishes shared "
        "graph state, and commits generated .grapher/shared output with a recursion guard."
    ),
    "docs/README.md": (
        "Documentation index and mental-model entrypoint for Neith. It links the active 0926-1 "
        "framework plan with architecture, usage, browser, development, and repository references; "
        "states the server-driven Go mental model; and explains Grapher/source-of-truth policy."
    ),
})

if __name__ == "__main__":
    base.main()
