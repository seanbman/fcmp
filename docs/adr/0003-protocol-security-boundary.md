# ADR 0003: Browser is a finite protocol interpreter

Status: Accepted
Date: 2026-09-10
Plan: `docs/DEVELOPMENT_PLAN_0926-1.md`

## Context

Neith needs rich server-directed interaction without making the browser a second application framework. A generic remote-JavaScript mechanism would reduce apparent implementation work but would create an unsafe, difficult-to-version execution boundary.

## Decision

The Neith browser runtime is a finite, versioned protocol interpreter. Protocol messages select known operations with validated payloads. The protocol must not execute arbitrary JavaScript source received from the server.

Forbidden protocol mechanisms include `eval`, `new Function`, unrestricted property traversal/execution, and a generic remote `exec` instruction.

The existing named custom-function mechanism is compatibility/advanced surface and must be constrained or replaced by explicit protocol primitives before 1.0.

## Consequences

- Protocol operations become an intentional compatibility surface.
- Go and browser contracts require mechanical drift detection and end-to-end contract tests.
- Unknown versions, operations, and malformed payloads fail closed.
- WSS is necessary transport protection but is not treated as justification for arbitrary code execution.
- Common UI effects should be represented as finite render/mutation/navigation/listener primitives.

## Alternatives rejected

- Sending JavaScript source over WebSocket and evaluating it.
- Growing an unversioned function-name dispatch table indefinitely.
- Moving application behavior into a browser-side Neith framework.

## Implementation references

- `dispatch.go`, `dispatch_payloads.go`: current Go wire model.
- `static/assets/api.ts`, `static/assets/neith_types.ts`: current browser dispatch contract.
- `handler.go`: current dispatch execution path.
