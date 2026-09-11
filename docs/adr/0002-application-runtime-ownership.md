# ADR 0002: First-class Application owns runtime

Status: Accepted
Date: 2026-09-10
Plan: `docs/DEVELOPMENT_PLAN_0926-1.md`

## Context

The current package uses package-global configuration and creates a new runtime for each `App` / `MiddleWareFn` mount. This makes the library usable, but it makes multi-route applications, lifecycle ownership, dependency injection, testing, and future session policy harder to reason about.

## Decision

Introduce a first-class `Application` that implements `http.Handler` and owns one runtime plus its configuration and route registrations.

Canonical direction:

```go
app := neith.New(...)
app.Route("/", home)
app.Route("/settings", settings)
http.ListenAndServe(":8080", app)
```

Routes registered on one application share that application's intended runtime boundary. Separately created applications remain isolated. Existing `App` and `MiddleWareFn` APIs remain compatibility wrappers during the pre-1.0 migration.

Package-global configuration must cease to be the canonical configuration path. Compatibility globals may exist temporarily but must not define the architecture of new APIs.

## Consequences

- Application lifecycle, sessions, state, event execution, protocol policy, uploads, security policy, and diagnostics gain an explicit owner.
- Multi-route applications can share one deliberate runtime boundary.
- Independent applications can be tested for isolation.
- Existing callers can migrate incrementally.
- Runtime creation must be refactored so handlers can attach to an existing application runtime rather than always creating their own.

## Alternatives rejected

- Keep one runtime per route forever.
- Introduce a process-global singleton application.
- Build a new routing ecosystem instead of implementing `http.Handler`.

## Implementation references

- `pkg.go`: current package-global configuration.
- `runtime.go`: runtime ownership.
- `handler.go`: current per-mount runtime creation.
- `page.go`: current `App` compatibility entry point.
