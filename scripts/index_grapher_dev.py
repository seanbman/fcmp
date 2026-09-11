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
        "Accepted protocol/security decision defining the browser as a finite versioned interpreter, "
        "rejecting arbitrary remote JavaScript, establishing protocol v1 validation, safe same-origin "
        "WebSocket defaults, bounded inbound messages, and server-issued opaque HttpOnly sessions shared "
        "by page, WebSocket, and upload traffic."
    ),
    "application.go": (
        "Canonical Application API. It owns an isolated runtime and ServeMux, shares one runtime across "
        "registered routes, implements http.Handler, exposes shutdown lifecycle, and offers application-"
        "local transport policy options including WebSocket message limits and explicit origin policy."
    ),
    "application_test.go": (
        "Application contract tests covering route serving, shared runtime within one application, "
        "isolation between applications, local configuration, idempotent shutdown, post-shutdown rejection, "
        "and closure/detachment of runtime-tracked connections."
    ),
    "runtime.go": (
        "Internal Application runtime ownership boundary. It owns handlers, sessions, listeners, state "
        "stores, configuration, cancellation context, closed state, tracked connection lifetime, and "
        "idempotent graceful shutdown."
    ),
    "handler.go": (
        "Runtime HTTP/WebSocket/upload bridge and bidirectional dispatch pipeline. Normal page requests "
        "establish/reuse a server-issued session cookie, WebSocket upgrades and uploads require that cookie, "
        "Application routes can share one runtime, legacy middleware remains isolated, and runtime cancellation "
        "terminates handler/ping pipelines."
    ),
    "conn.go": (
        "Runtime-owned WebSocket transport. Gorilla's same-origin policy is the default unless explicitly "
        "overridden, inbound frame size is bounded by application configuration, messages are rejected unless "
        "they carry the current protocol version and an allowed browser-to-server operation, and connection "
        "reads/writes stop with Application shutdown."
    ),
    "session.go": (
        "Client-session registry preserving one active socket per opaque session while allowing state to "
        "survive connection replacement. It also enumerates active connections for Application shutdown."
    ),
    "session_http.go": (
        "Server-side HTTP session boundary. It generates cryptographically random 32-byte URL-safe opaque "
        "session identifiers, reads them only from the configured cookie, and issues HttpOnly SameSite=Lax "
        "cookies that become Secure automatically on direct HTTPS or when forced behind trusted TLS termination."
    ),
    "session_http_test.go": (
        "Security contract tests for server-issued sessions: random opaque cookie issuance, HttpOnly and "
        "SameSite=Lax policy, reuse of existing sessions, Secure behavior for HTTPS/proxy configuration, "
        "and automatic session establishment on a normal Application page response."
    ),
    "errors.go": (
        "Stable application lifecycle, dispatch/event, connection, and cache errors. ErrApplicationClosed "
        "identifies work rejected after Application shutdown begins."
    ),
    "dispatch.go": (
        "Go wire-contract definition. ProtocolVersion=1 is explicit in every new Dispatch via JSON field v; "
        "the server validates version and a finite inbound operation allowlist before browser frames may reach "
        "handlers. The flat payload is transitional v1 compatibility surface."
    ),
    "dispatch_test.go": (
        "Go protocol contract tests locking the v1 JSON field, automatic ProtocolVersion initialization, "
        "browser-to-server operation allowlist, and render/listener serialization."
    ),
    "pkg.go": (
        "Neith configuration definitions and legacy global compatibility path. Application-local config now "
        "includes WebSocket message limits, optional explicit Origin policy, and server-session cookie name, "
        "path, and Secure policy while retaining local normalization without mutating global state."
    ),
    "static/assets/neith_types.ts": (
        "Browser TypeScript wire contract exporting PROTOCOL_VERSION=1 and requiring Dispatch.v alongside "
        "the finite operation payloads, synchronized with Go dispatch.go."
    ),
    "static/assets/api.ts": (
        "Browser finite dispatch router. It rejects missing/unsupported protocol versions before executing "
        "redirect/render/class/DOM/custom/ping behavior and requires outbound responses to retain v1."
    ),
    "static/assets/socket.ts": (
        "Browser WebSocket lifecycle owner. It derives same-route ws/wss URLs, reconnects with capped backoff, "
        "and intentionally owns no session identifier: the browser automatically carries Neith's HttpOnly "
        "server-issued cookie on same-origin upgrades."
    ),
    "static/assets/uploads.ts": (
        "Browser multipart upload helper. Files travel over same-origin HTTP with credentials while the "
        "HttpOnly Neith session cookie supplies session binding; no session identifier is read from JavaScript "
        "or exposed in the upload URL."
    ),
    "static/assets/tests/setup.ts": (
        "Jest integration setup that adds the current protocol version to legacy mock-server fixture frames "
        "only inside tests, preserving strict production version validation while keeping behavior fixtures concise."
    ),
    "static/assets/tests/protocol.test.ts": (
        "Focused browser wire-contract tests proving missing/unsupported protocol versions execute no operation "
        "and send no reply, while valid v1 ping responses preserve the negotiated version."
    ),
    "static/assets/jest.config.js": (
        "Jest/ts-jest browser-runtime configuration. It loads the protocol fixture setup and uses anchored "
        "test-facing module mappings so protocol tests resolve source modules without overbroad path rewriting."
    ),
    "static/assets/package.json": (
        "Browser development manifest defining serialized Jest coverage verification and reproducible esbuild "
        "bundling of index.ts into the embedded neith.min.js artifact."
    ),
    ".github/workflows/grapher-index.yml": (
        "Dev verification workflow gating publication on Go tests and browser Jest tests, rebuilding the "
        "embedded browser bundle, running canonical Grapher validation/audit/publication, and committing generated "
        "bundle plus shared graph state together under a recursion guard."
    ),
    "AGENTS.md": (
        "Repository agent policy for plan 0926-1: read active plans/ADRs/API classification, preserve Application "
        "runtime and finite-protocol invariants, use Grapher continuously, and synchronize tests/docs/generated assets."
    ),
    "scripts/index_grapher_dev.py": (
        "Development Grapher entrypoint augmenting the canonical full-repository index with semantic summaries "
        "for dev-only planning, architecture, protocol, lifecycle, security, and test artifacts before validation, "
        "audit, search verification, and publication."
    ),
    "docs/README.md": (
        "Neith documentation index and mental-model entrypoint linking the active framework plan with architecture, "
        "usage, browser, development and repository references plus Grapher/source-of-truth policy."
    ),
})

if __name__ == "__main__":
    base.main()
