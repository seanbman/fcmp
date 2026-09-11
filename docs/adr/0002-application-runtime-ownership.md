# ADR 0002: First-class Application owns runtime

Status: Accepted / implemented in Phase 1
Date: 2026-09-10
Plan: `docs/DEVELOPMENT_PLAN_0926-1.md`

## Context

The legacy package uses package-global configuration and creates a new runtime for each `App` / `MiddleWareFn` mount. This makes the library usable, but it makes multi-route applications, lifecycle ownership, dependency injection, testing, and future session policy harder to reason about.

## Decision

A first-class `Application` implements `http.Handler` and owns one runtime plus its configuration, route registrations, active transport lifetime, and shutdown boundary.

Canonical direction:

```go
app := neith.New(...)
app.Route("/", home)
app.Route("/settings", settings)

server := &http.Server{Addr: ":8080", Handler: app}
// Start server, then during process shutdown:
_ = app.Shutdown(ctx)
_ = server.Shutdown(ctx)
```

Routes registered on one application share that application's intended runtime boundary. Separately created applications remain isolated. Existing `App` and `MiddleWareFn` APIs remain compatibility entry points during the pre-1.0 migration.

Package-global configuration is not the canonical configuration path. Compatibility globals may exist temporarily but do not define the architecture of new APIs.

Application shutdown is idempotent. Once shutdown begins, the runtime context is cancelled, new application requests are rejected, active WebSocket connections are closed, runtime-owned connection work drains, and `Application.Done()` becomes observable to framework internals and host code.

## Consequences

- Application lifecycle, sessions, state, event execution, protocol policy, uploads, security policy, and diagnostics have an explicit owner.
- Multi-route applications share one deliberate runtime boundary.
- Independent applications remain isolated and are directly testable for isolation.
- Active connections have an application-owned lifetime instead of surviving independently of process/runtime shutdown.
- Handler pipelines and cache-cleanup waits can observe runtime cancellation rather than leaking indefinitely after shutdown.
- Existing callers can migrate incrementally.
- Future protocol/session work has a concrete owner on which to place secure policy.

## Alternatives rejected

- Keep one runtime per route forever.
- Introduce a process-global singleton application.
- Build a new routing ecosystem instead of implementing `http.Handler`.
- Treat WebSocket connection lifetime as independent from application lifetime.

## Implementation references

- `application.go`: canonical `Application`, route registration, HTTP serving, `Done`, `Shutdown`, and `Close`.
- `runtime.go`: runtime ownership, cancellation context, tracked connection lifetime, idempotent shutdown.
- `handler.go`: shared-runtime route bridge and runtime-aware handler pipeline termination.
- `conn.go`: connection tracking, runtime-aware reads/writes, and shutdown-safe cleanup.
- `session.go`: active-connection enumeration used by shutdown.
- `application_test.go`: route sharing, application isolation, local config, shutdown, and tracked-connection contracts.
- `pkg.go`: legacy package-global configuration compatibility path.
- `page.go`: legacy `App` compatibility entry point.
