# AGENTS.md

## Purpose

Neith is becoming a Go server-driven web framework with a TypeScript browser protocol runtime. Agents working in this repository must keep implementation, tests, documentation, generated browser assets, ADRs, the active development plan, and the Grapher knowledge graph aligned.

## Read first

Before changing behavior, read the smallest relevant set:

1. `docs/DEVELOPMENT_PLAN_0926-1.md` for active framework direction and sequencing.
2. `docs/adr/` for accepted architectural decisions.
3. `docs/API_SURFACE_0926-1.md` for canonical/compatibility/internal API classification.
4. `docs/ARCHITECTURE.md` for current subsystem boundaries and runtime/session semantics.
5. `docs/USAGE.md` for the current public API contract.
6. `docs/BROWSER_CLIENT.md` for WebSocket/browser changes.
7. `docs/DEVELOPMENT.md` for tests and generated-file rules.
8. Search Grapher for the subsystem being changed.

## Grapher is part of the repository workflow

Install/synchronize the current Grapher tool from `seanbman/grapher`:

```sh
pip install 'git+https://github.com/seanbman/grapher.git@main'
grapher sync
grapher search "<concept being changed>" --mode lexical
```

Do not create path-only knowledge nodes. Any new tracked source/document/media file must be deeply understood and given semantic `content`, then related to the subsystem it implements, tests, documents, or generates.

After meaningful changes:

```sh
grapher scan .
grapher validate
grapher audit
grapher publish
```

A change is not graph-complete if a recognized tracked file remains pending. Files skipped by Grapher's default extension classifier still need explicit semantic nodes when they are meaningful repository artifacts.

## Architectural invariants

Preserve these unless the change deliberately redesigns them and updates ADRs, docs, tests, and Grapher:

- `Application` is the canonical owner of a runtime and its routes. Routes inside one Application share that runtime boundary; separately created Applications are isolated.
- Legacy `App` / `MiddleWareFn` mounts retain isolated-runtime behavior as compatibility surface during migration.
- A browser client session may survive a single WebSocket connection and has only one active connection at a time.
- State/cache and event listeners are scoped inside their owning runtime/client-session boundary.
- Go owns application behavior, rendering, state decisions, and event handlers; the browser executes a finite known protocol.
- Arbitrary server-supplied JavaScript execution is not an acceptable protocol feature.
- File bytes use multipart HTTP; event WebSocket messages carry upload metadata.
- Current `Dispatch` and `static/assets/neith_types.ts` are two sides of the wire contract until Protocol v1 replaces them.
- `net/http` remains the host integration boundary.
- Generated assets are not primary edit targets.

## Generated files

Do not hand-edit:

- `static/assets/neith.min.js` — generated from TypeScript sources.
- `examples/readme-setup/dashboard_templ.go` — generated from `dashboard.templ`.
- generated Tailwind/Sass outputs when their source exists.

Rebuild and commit generated outputs whenever package consumers would otherwise receive stale behavior.

## Verification

For Go changes:

```sh
gofmt -w <changed-go-files>
go test ./...
```

For browser changes:

```sh
cd static/assets
npm install
npm test
```

For protocol changes, verify both suites and rebuild `neith.min.js`.

Runtime/session/state changes should add or update isolation and race-sensitive tests. Public API changes require documentation/example updates. Protocol changes require contract coverage.

## Documentation discipline

Update the document that owns the concept rather than growing the root README indiscriminately. Record high-cost architectural choices in `docs/adr/`. Keep `docs/REPOSITORY_MAP.md` current when files/subsystems move. When behavior and prose disagree, executable code/tests win temporarily, but documentation and Grapher must be corrected in the same workstream.
