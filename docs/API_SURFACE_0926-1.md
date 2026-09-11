# Neith API Surface Classification — 0926-1

Status: active migration inventory
Date: 2026-09-10
Plan: `DEVELOPMENT_PLAN_0926-1.md`

This inventory prevents accidental compatibility commitments while Neith moves toward 1.0. It classifies concepts rather than promising that every current symbol will retain its exact spelling.

## Canonical direction

These are the concepts normal application documentation should converge on:

| Concept | Direction |
| --- | --- |
| `Application` | Canonical owner of routes, runtime, config, policy, lifecycle |
| `New(...)` | Canonical application constructor |
| `Application.Route(...)` | Canonical multi-route registration |
| `Component` | Canonical renderer-neutral UI contract |
| `View` | Canonical interactive component wrapper |
| `Event` access | Canonical browser-intent input model; exact ergonomic facade still to be designed |
| `State` | Canonical scoped server-state concept; replaces cache vocabulary after migration |
| selector target operations | Canonical render/mutation targeting; exact names finalized in Phase 5 |
| `Page` / page options | Supported document-shell customization |

## Compatibility surface

These remain usable while their replacements are introduced, but new documentation should not expand dependence on them:

| Current surface | Migration direction |
| --- | --- |
| `App(...)` | Thin convenience wrapper over `Application` |
| `SetConfig` / package-global config | Application-owned options/config |
| `MiddleWareFn` | Application/runtime-owned internal mounting path |
| `Cache[T]`, `NewCache`, `UseCache` | `State` API with explicit scope |
| `Click`, `Change`, `Input`, `Submit`, `KeyDown` aliases | One canonical event naming family |
| explicit tag/element render-target families | Concise selector-based operations |
| `FnErr` | Application error boundary/model |

## Advanced surface

Useful escape hatches or lower-level concepts that should not dominate the quick start:

- raw dispatch construction and payload details;
- custom browser extension registration;
- low-level event listener registration;
- raw page/client-script replacement;
- transport/session diagnostics;
- direct runtime/protocol extension points once formalized.

## Candidate internal surface

Implementation concepts that should move behind a stable boundary where compatibility allows:

- `FnComponent` transport mechanics;
- `HandleFn` spelling/type as currently exposed;
- `FnRender` / `FnDOM` / `FnClass` wire-oriented types;
- handler IDs and connection IDs;
- runtime lookup/fallback machinery;
- transport connection implementation;
- protocol function strings and dispatch routing internals.

## Rules during migration

1. New examples use the canonical direction whenever that API exists.
2. Compatibility APIs may delegate to canonical internals but should not acquire unrelated new responsibilities.
3. Candidate-internal APIs receive no new convenience aliases.
4. Any removal or semantic break is recorded in the changelog before 1.0.
5. Protocol wire compatibility and Go source compatibility are tracked separately.
6. Grapher should relate replacement concepts to the compatibility surface they supersede.

## Current architectural invariants to preserve while refactoring

- Existing `App` callers continue to receive an isolated runtime unless deliberately migrated to a shared `Application`.
- Separate `Application` instances are isolated.
- Routes inside one `Application` share that application's runtime boundary.
- Go remains authoritative for application behavior.
- Browser code executes finite known operations, not server-supplied source.
- `net/http` remains the host integration boundary.
