# Neith Documentation

This directory is the maintainers' and users' guide to the Neith repository. The root `README.md` remains the public package overview and API-oriented introduction; the documents here separate architecture, practical usage, browser behavior, development workflow, repository structure, and framework planning so each concern can evolve without turning one file into a monolith.

**Active framework roadmap:** [`DEVELOPMENT_PLAN_0926-1.md`](DEVELOPMENT_PLAN_0926-1.md).

## Documentation map

| Document | Purpose |
| --- | --- |
| [`DEVELOPMENT_PLAN_0926-1.md`](DEVELOPMENT_PLAN_0926-1.md) | Active pre-1.0 framework development plan: API simplification, Application ownership, State, deterministic events, secure versioned browser protocol, tiny client interpreter, security, DX, ADRs, Grapher, CI, and release sequencing. |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Runtime boundaries, HTTP/WebSocket lifecycle, dispatch protocol, rendering, events, cache, uploads, and asset flow. |
| [`USAGE.md`](USAGE.md) | Installation, mounting an app, views, events, DOM effects, state, uploads, configuration, and production guidance. |
| [`BROWSER_CLIENT.md`](BROWSER_CLIENT.md) | TypeScript client modules, WebSocket lifecycle, dispatch processing, event serialization, hooks, uploads, and generated bundle. |
| [`DEVELOPMENT.md`](DEVELOPMENT.md) | Toolchain, Make targets, tests, generated assets, templ example, release flow, and contribution checks. |
| [`REPOSITORY_MAP.md`](REPOSITORY_MAP.md) | File-by-file map of the Go package, UI package, browser client, tests, examples, notes, assets, and configuration. |

The older focused notes remain useful deep references:

- [`../notes/component/README.md`](../notes/component/README.md) is the detailed `Component` / `FnComponent` reference.
- [`../notes/cache/README.md`](../notes/cache/README.md) is the detailed typed cache reference.
- [`../examples/readme-setup/README.md`](../examples/readme-setup/README.md) documents the runnable example.

## Mental model

Neith is a server-rendered interaction layer for Go. Application code renders a value implementing:

```go
type Component interface {
    Render(ctx context.Context, w io.Writer) error
}
```

`View` / `FnComponent` adds instructions describing where that HTML should go and which browser events should call back into Go. `App` serves the page and establishes an isolated runtime. The browser bundle opens a WebSocket with a stable `neith_id`, receives dispatch messages, mutates the DOM, and posts event dispatches back to the server.

The current implementation is the baseline, while `DEVELOPMENT_PLAN_0926-1.md` defines the intended framework evolution. In particular, the target direction is a first-class `Application`, explicit `State`, deterministic per-session event execution, secure server-issued sessions, a versioned protocol, and a tiny trusted browser interpreter rather than a second client-side application framework.

The useful rule of thumb is:

1. **HTML stays server rendered.** Use `templ`, `neith.HTML`, `ui`, or any compatible renderer.
2. **Behavior is declared in Go.** Attach browser events with `OnClick`, `OnSubmit`, `On`, or lower-level `WithEvents`.
3. **The browser is a thin runtime.** It applies a finite Neith UI protocol and serializes browser events back to Go; arbitrary server-supplied JavaScript execution is not part of the target architecture.
4. **State is server-side and scoped.** Current generic caches belong to a browser client ID inside one mounted runtime; the framework plan promotes this into an explicit state model.

## Grapher index

The repository is semantically indexed with [seanbman/grapher](https://github.com/seanbman/grapher). The committed shared graph lives under `.grapher/shared/`; local mutable Grapher state remains in `.grapher/` and should be synchronized from the shared graph before making graph-aware changes.

Typical local workflow:

```sh
pip install 'git+https://github.com/seanbman/grapher.git@main'
grapher sync
grapher search "websocket reconnect session state protocol" --mode lexical
grapher validate
grapher audit
```

The index contains file-level semantic nodes plus architectural nodes and relationships. Path-only entries are not considered complete: source files, tests, docs, configuration, generated assets, and branding/static artifacts all carry an explanation of their role in Neith. Framework development should additionally connect ADRs, invariants, public APIs, protocol operations, security boundaries, tests, and migration/deprecation relationships.

## Source-of-truth order

When documentation and implementation disagree, prefer this order while correcting the drift:

1. executable Go/TypeScript behavior and tests;
2. accepted ADRs and active development-plan decisions for intended architecture;
3. public types and doc comments;
4. the documents in this directory;
5. root README examples and older focused notes;
6. generated/minified artifacts.

Generated files are evidence of a build, not the preferred place to understand or edit behavior. In particular, edit the TypeScript sources rather than `static/assets/neith.min.js`, edit source styles rather than generated/minified CSS, and edit `dashboard.templ` rather than `dashboard_templ.go`.
