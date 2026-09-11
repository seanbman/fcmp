# ADR 0001: Server-owned framework thesis

Status: Accepted
Date: 2026-09-10
Plan: `docs/DEVELOPMENT_PLAN_0926-1.md`

## Context

Neith is evolving from a server-rendered interaction library into a framework. The redesign needs a stable boundary so developer-experience improvements do not accidentally create a second application architecture in the browser.

## Decision

Neith follows this thesis:

> Write ordinary Go. Render ordinary components. Neith handles interactivity.

Application behavior, rendering decisions, state, authorization, and event handling are server-owned. The browser is a small, finite, versioned protocol interpreter. Neith remains compatible with `net/http` and renderer-neutral; `templ` is a first-class integration, not a required runtime.

## Consequences

- Public APIs are judged primarily by readability in normal Go application code.
- Browser-side application state/framework abstractions are out of scope.
- Arbitrary JavaScript received over the transport is not an acceptable protocol feature.
- Framework features should compose with standard Go middleware and HTTP infrastructure.
- New abstractions must justify themselves against the six-month readability test in plan 0926-1.

## Alternatives rejected

- A Go-flavored React clone with browser-owned application behavior.
- A client SPA framework with Neith acting primarily as an API transport.
- A framework-specific HTTP universe that replaces `net/http`.

## Implementation references

- `component.go`, `view.go`: server-rendered component/view model.
- `handler.go`, `runtime.go`: current runtime and transport orchestration.
- `static/assets/`: current browser runtime to be reduced toward the finite interpreter model.
