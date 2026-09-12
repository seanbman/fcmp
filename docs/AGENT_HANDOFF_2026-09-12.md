# Neith Agent Handoff — 2026-09-12

This is the compact operational handoff for the next agent working on `seanbman/neith`.

## Branch and authority

- Work on `dev` unless the operator explicitly says otherwise.
- Do not open a PR unless asked. Current work has been committed directly to `dev`.
- Read `AGENTS.md`, `docs/DEVELOPMENT_PLAN_0926-1.md`, `docs/API_SURFACE_0926-1.md`, and ADRs 0001–0003 before changing architecture.
- Use Grapher continuously. Any substantive code/architecture change must keep semantic summaries, tests, docs, generated browser assets, and `.grapher/shared` synchronized.
- Keep operator-facing chat compact; put durable detail in the repository.

## Framework thesis

The governing sentence is:

> **Write ordinary Go. Render ordinary components. Neith handles interactivity.**

Do **not** turn Neith into Go React. Go owns application behavior. The browser is a small trusted interpreter for an explicit protocol, not a place to ship arbitrary application logic.

Renderer neutrality and `net/http` compatibility are deliberate constraints.

## Phase 0 — established

Architecture decisions and API migration boundaries are documented:

- `docs/adr/0001-framework-thesis.md`
- `docs/adr/0002-application-runtime-ownership.md`
- `docs/adr/0003-protocol-security-boundary.md`
- `docs/API_SURFACE_0926-1.md`

The public direction is a first-class `Application`; package-global APIs are compatibility surface, not the desired 1.0 architecture.

## Phase 1 — Application/runtime ownership implemented

`application.go` introduces the canonical `Application` API. An application owns its runtime, config and `http.ServeMux`. Routes registered on one application deliberately share one runtime; separate applications remain isolated.

Configuration normalization was separated from legacy global mutation. `New(...)` can construct app-local configuration without rewriting package-global state. Legacy `SetConfig`, `App`, and `MiddleWareFn` remain compatibility paths.

Runtime lifecycle/shutdown work is present and documented in ADR 0002. Shutdown is intended to cancel runtime work, close tracked connections, reject new work, and be idempotent. Tests cover route sharing, app isolation, local config, shutdown behavior and connection cleanup.

Important invariant: do not accidentally return to “one runtime per route” for the canonical `Application` path.

## Phase 2 — protocol/security work in progress

The accepted security model is:

1. Browser preloads only Neith's finite trusted runtime.
2. Go sends explicit protocol commands/data.
3. No `eval`, `new Function`, generic remote execution, or arbitrary server-supplied JavaScript.
4. Every wire frame is versioned. Current protocol is v1.
5. WebSocket origin policy, authentication/session binding, message bounds and operation allowlists are enforced at boundaries.
6. Session identity is server-issued and opaque; JavaScript does not own it.

Current transport/session work includes server-issued opaque HttpOnly cookies, same-origin WebSocket defaults, bounded inbound WebSocket messages, protocol-version checks, inbound operation allowlisting, and upload/session alignment. Browser socket URLs no longer carry a client/session ID; the same-origin cookie binds page, WebSocket and upload traffic.

### Protocol v1 contract

Go `Dispatch` now has `ProtocolVersion = 1` and serializes through a versioned envelope. The current contract is moving away from exposing the historical internal flat dispatch representation on the wire. Strict decoding rejects unsupported versions and unknown envelope/payload fields.

`dispatch_test.go` was updated to assert the v1 envelope (`v`, `type`, `payload`) and to ensure legacy/internal fields such as `function`, `buf`, and `conn` do not leak into JSON. It also tests unknown-field rejection, unsupported-version rejection and the inbound operation allowlist.

Browser `static/assets/protocol.ts` is the codec/validation boundary. `static/assets/socket.ts` was changed so incoming WebSocket JSON passes through `decodeMessage(...)` before `API.Process(...)`. `static/assets/api.ts` was changed so outbound replies pass through `encodeMessage(...)` before `ws.send(...)`.

This is important: **do not bypass `protocol.ts` by casting raw `JSON.parse` output directly to `Dispatch`, and do not send raw internal `Dispatch` objects directly over the socket.**

The browser `API` still contains the transitional finite operation router (`render`, `class`, `dom`, `redirect`, `ping`, and currently `custom`). `custom` is legacy/high-risk surface and should be constrained/retired rather than expanded. Never replace it with arbitrary JS execution.

## Verification and CI

`.github/workflows/grapher-index.yml` is the dev verification gate. The intended chain is:

1. Go tests.
2. Browser/Jest protocol/runtime tests.
3. Rebuild the embedded browser bundle (`static/assets/neith.min.js`).
4. Run canonical Grapher index/validate/audit/publish.
5. Commit generated bundle and `.grapher/shared` state under the recursion guard.

A stale Go protocol-shape test briefly broke CI after the wire format changed; that test has been corrected. The WebSocket codec integration was then committed. At handoff time the latest browser/API commit had triggered verification and was still running, so **the next agent's first action must be to inspect the latest `dev` Actions run and fix any failure before advancing architecture**. Do not assume green status from this document.

## Grapher

`scripts/index_grapher_dev.py` extends the canonical indexer with semantic summaries for the active plan, ADRs, Application/runtime ownership, session/security work, protocol files, browser tests and CI. Keep this file updated for new architectural artifacts.

The graph is an architectural memory, not merely a file inventory. Preserve relationships/invariants around Application ownership, finite protocol execution, security boundaries and API migration.

## Immediate next work

After the current verification chain is green, finish Phase 2 cleanly before declaring it complete. Confirm Go↔browser protocol contract coverage, codec use at every transport boundary, generated bundle synchronization, strict inbound validation, upload/session consistency, origin policy and message-size behavior.

Then begin **Phase 3 — Tiny Browser Interpreter** from `docs/DEVELOPMENT_PLAN_0926-1.md`: collapse browser behavior toward a small explicit instruction set rather than adding framework magic. The intended conceptual operations are things such as `render`, constrained `mutate`, `listen`, `navigate`, `upload`, `ping`, and `error`. Mutation should use an allowlisted operation vocabulary; selector-targeted server APIs will eventually become the clean Go-facing abstraction.

Do not jump ahead into state/event redesign until Phase 2 is actually verified unless a necessary protocol change requires it.

## Later plan anchors

After Phase 3:

- Phase 4: State semantics and deterministic event execution. Conceptually rename `Cache` to `State`; define request/session/application scopes; serialize event execution per client session by default while allowing sessions to run concurrently; define cancellation/disconnect behavior.
- Phase 5: Public API elegance — selector operations (`Into`, `Append`, `Replace`, `Remove`), event/request facade, typed forms/input, error boundary, renderer-neutral templ ergonomics.
- Phase 6: DX — dev overlay/target validation, canonical examples, documentation and eventually a tiny CLI.
- Phase 7: pre-1.0 hardening — internalize transport/protocol machinery, remove/reduce aliases, release discipline and compatibility review.

Explicit non-goals remain: routing magic, ORM integration, DI containers, React-style hooks, giant component libraries and complex code generation.

## Design test

For every proposed feature, ask:

> **Does this make an interactive Go application easier to read six months later?**

If not, it probably does not belong in Neith's core.
