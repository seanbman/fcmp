#!/usr/bin/env python3
"""Development-branch Grapher entrypoint for Neith.

Extends the canonical full-repository indexer with semantic summaries for
framework-planning and implementation artifacts that exist on dev before
invoking the normal index/validate/audit/publish pipeline.
"""

import index_grapher as base

base.SUMMARIES.update({
    "docs/AGENT_HANDOFF_2026-09-12.md": (
        "Current Neith implementation handoff for successor agents. It records branch and repository policy, "
        "the framework thesis, completed Phase 0 and Phase 1 architecture, active Phase 2 protocol/security "
        "work, strict Go/browser codec boundaries, verification and Grapher requirements, immediate Phase 2 "
        "closure work, Phase 3 browser-interpreter direction, later plan anchors, and explicit non-goals."
    ),
    "docs/DEVELOPMENT_PLAN_0926-1.md": (
        "Neith pre-1.0 framework development plan 0926-1. It converts the 2026-09-10 architecture and "
        "developer-experience strategy into staged implementation work: first-class Application ownership, "
        "state semantics, deterministic events, a secure versioned Go/browser protocol, a tiny trusted browser "
        "instruction interpreter, WebSocket/session/upload hardening, API simplification, ADRs, CI gates, "
        "documentation, Grapher governance, examples, observability, and release discipline."
    ),
    "docs/API_SURFACE_0926-1.md": "Pre-1.0 API migration inventory classifying canonical, compatibility, advanced and candidate-internal Neith concepts.",
    "docs/adr/0001-framework-thesis.md": "Accepted Neith framework thesis: ordinary Go owns application behavior and rendering while a thin browser runtime supplies interactivity.",
    "docs/adr/0002-application-runtime-ownership.md": "Accepted Application ownership decision: one runtime per Application, shared by its routes, isolated between applications, with explicit lifecycle/shutdown.",
    "docs/adr/0003-protocol-security-boundary.md": "Accepted finite versioned browser protocol and security-boundary decision rejecting arbitrary remote JavaScript execution.",
    "application.go": "Canonical Application API owning isolated runtime, configuration, routes, lifecycle and transport policy.",
    "application_test.go": "Application contract tests for routing, shared runtime, isolation, configuration and shutdown behavior.",
    "runtime.go": "Internal Application runtime ownership boundary including handlers, sessions, state, cancellation and connection lifetime.",
    "handler.go": "HTTP/WebSocket/upload bridge binding Application routes to runtime dispatch and server-issued sessions.",
    "conn.go": "Runtime-owned bounded WebSocket transport enforcing origin, protocol version and inbound operation policy.",
    "session.go": "Client-session registry preserving one active connection per opaque server-issued session and supporting reconnect replacement.",
    "session_http.go": "HTTP session boundary generating and issuing opaque HttpOnly server-side session cookies.",
    "session_http_test.go": "Security tests for session cookie issuance, reuse, HTTPS Secure policy and Application page establishment.",
    "errors.go": "Stable lifecycle, dispatch, connection and state/cache errors including ErrApplicationClosed.",
    "dispatch.go": "Go protocol-v1 wire contract and strict versioned envelope codec with finite inbound operation validation.",
    "dispatch_test.go": "Go protocol contract tests for v1 envelope shape, strict unknown-field rejection, version validation and inbound allowlisting.",
    "pkg.go": "Neith configuration and legacy-global compatibility path with Application-local transport/session policy.",
    "static/assets/neith_types.ts": "Browser TypeScript protocol types synchronized with Go protocol v1.",
    "static/assets/protocol.ts": "Browser protocol-v1 codec and strict validation boundary translating wire envelopes to internal finite dispatch operations and back.",
    "static/assets/api.ts": "Browser finite operation router; outbound replies are encoded through the protocol codec before WebSocket transmission.",
    "static/assets/socket.ts": "Browser WebSocket lifecycle owner; inbound raw JSON is decoded and validated by protocol.ts before API execution.",
    "static/assets/uploads.ts": "Same-origin multipart upload helper bound to the server-issued HttpOnly Neith session cookie.",
    "static/assets/tests/setup.ts": "Jest integration setup for current protocol fixtures.",
    "static/assets/tests/protocol.test.ts": "Focused browser protocol contract tests for version validation and v1 response behavior.",
    "static/assets/jest.config.js": "Jest/ts-jest browser-runtime verification configuration.",
    "static/assets/package.json": "Browser development manifest defining tests and reproducible embedded bundle generation.",
    ".github/workflows/grapher-index.yml": "Dev verification workflow gating generated bundle and Grapher publication on Go/browser verification.",
    "AGENTS.md": "Repository agent policy requiring plan/ADR/API awareness, finite-protocol invariants, continuous Grapher use and synchronized artifacts.",
    "scripts/index_grapher_dev.py": "Development Grapher entrypoint adding semantic summaries for active architecture and implementation artifacts.",
    "docs/README.md": "Neith documentation index and mental-model entrypoint linking active plans, architecture, usage and repository references."
})

if __name__ == "__main__":
    base.main()
