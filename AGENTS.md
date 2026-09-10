# AGENTS.md

## Purpose

Neith is a Go server-rendered interaction library with a TypeScript browser runtime. Agents working in this repository must keep implementation, tests, documentation, generated browser assets, and the Grapher knowledge graph aligned.

## Read first

Before changing behavior, read the smallest relevant set:

1. `docs/README.md` for documentation navigation and source precedence.
2. `docs/ARCHITECTURE.md` for subsystem boundaries and runtime/session semantics.
3. `docs/USAGE.md` for the public API contract.
4. `docs/BROWSER_CLIENT.md` for WebSocket/browser changes.
5. `docs/DEVELOPMENT.md` for tests and generated-file rules.
6. Search Grapher for the subsystem being changed.

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

Preserve these unless the change deliberately redesigns them and updates docs/tests:

- Each `App` / `MiddleWareFn` mount owns an isolated runtime.
- A browser client session may survive a single WebSocket connection and has only one active connection at a time.
- Caches and event listeners are scoped inside a runtime/client session boundary.
- Go owns rendering and handler logic; the browser runtime applies dispatches and serializes events.
- File bytes use multipart HTTP; event WebSocket messages carry upload metadata.
- `Dispatch` and `static/assets/neith_types.ts` are two sides of the same wire contract.
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

## Documentation discipline

Update the document that owns the concept rather than growing the root README indiscriminately. Keep `docs/REPOSITORY_MAP.md` current when files/subsystems move. When behavior and prose disagree, executable code/tests win temporarily, but documentation and Grapher must be corrected in the same workstream.