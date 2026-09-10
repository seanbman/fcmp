# Development Guide

Neith spans a Go package, a TypeScript browser runtime, an optional Go `ui` package, and a runnable `templ` example. Changes that cross the WebSocket protocol often need coordinated Go and TypeScript work.

## Toolchain

Minimum/source-declared requirements:

- Go 1.21.5 or newer compatible Go toolchain;
- Node/npm for browser-client tests;
- TypeScript for client compilation;
- esbuild for the minified browser bundle (`./es-build` in the Makefile);
- Tailwind CLI (`./tailwindcss`) and Sass when rebuilding all style assets;
- `templ` for regenerating the example component;
- Delve for the optional headless debug target.

The core Go module directly depends on Gorilla WebSocket, Charmbracelet Log, and Google UUID. Browser development dependencies live under `static/assets/package.json` and include Jest, ts-jest, jsdom, jest-websocket-mock, and TypeScript.

## Repository setup

```sh
git clone https://github.com/seanbman/neith.git
cd neith
go mod download
cd static/assets
npm install
cd ../..
```

If you are changing only the Go package, Node dependencies are unnecessary until you run the full test suite or rebuild the browser bundle.

## Test suites

The Makefile's `test` target runs both sides:

```sh
make test
```

Equivalent commands:

```sh
go test ./... -v

cd static/assets
npm install
npm test
```

Browser tests run Jest serially (`-i`) with coverage. Go tests are colocated with the package and `ui` code.

### Test responsibility map

| Test file | Primary contract |
| --- | --- |
| `cache_test.go` | Generic cache creation/use, type/key behavior, timeouts, callbacks/history, and isolation semantics. |
| `component_test.go` | `FnComponent` rendering, targeting, dispatch metadata, events, and helper behavior. |
| `conn_test.go` | Connection/session publication and lifecycle behavior. |
| `dispatch_test.go` | Dispatch envelope/default behavior and payload state. |
| `events_test.go` | Event payload decoding, upload metadata, and submitter access. |
| `page_test.go` | Generated page shell, options, and embedded assets. |
| `runtime_test.go` | Runtime construction/isolation. |
| `session_test.go` | Active connection replacement and session registry behavior. |
| `upload_test.go` | Multipart upload limits/storage/metadata. |
| `view_test.go` | High-level `ViewOption` mappings to `FnComponent` behavior. |
| `ui/component_test.go` | Renderer-agnostic UI output, escaping, options, forms/tables. |
| `static/assets/tests/index.test.ts` | End-to-end browser dispatch, DOM application, event serialization, reconnects, uploads, hooks, and errors. |

Protocol changes should normally add or adjust tests on both sides.

## Running the example

```sh
make example
```

The example runs from `examples/readme-setup` and defaults to `:8080`. Override the address with:

```sh
make example EXAMPLE_ADDR=:9090
```

The example combines Neith with a generated `templ` component and its own static CSS. It is the best manual smoke test for the README-style setup.

## Generating the templ example

Edit:

```text
examples/readme-setup/dashboard.templ
```

Then regenerate:

```sh
make example-templ
```

The generated file:

```text
examples/readme-setup/dashboard_templ.go
```

should be treated as a build artifact. Review it for expected regeneration, but do not implement source changes directly in it.

## Browser asset workflow

### TypeScript development

For a compiler watch loop:

```sh
make tsc
```

The browser source modules are under `static/assets/*.ts` and tests under `static/assets/tests/`.

### Bundle only

```sh
make bundle
```

This runs esbuild from `static/assets/index.ts` and replaces `static/assets/neith.min.js` with a minified bundle.

### Full assets

```sh
make assets
```

The target performs:

1. `templ` generation;
2. TypeScript compilation;
3. esbuild bundling into `neith.min.js`;
4. Tailwind build/minification;
5. Sass compilation.

Repository-local `./es-build` and `./tailwindcss` executables are expected by the Makefile when those targets are used. If they are not present in a checkout, install/provide compatible binaries or invoke equivalent installed tooling deliberately rather than silently committing stale generated output.

### Styles

The neutral package stylesheet embedded by Go is:

```text
static/assets/neith-ui.css
```

Tailwind input/output live at:

```text
static/assets/stylesheets/tailwind.css
static/assets/stylesheets/tailwind.min.css
```

Sass source/output locations are:

```text
static/assets/sass/
static/assets/stylesheets/
```

Do not confuse the neutral UI stylesheet with generated Tailwind/Sass assets. `page.go` embeds `neith-ui.css` and `neith.min.js` specifically.

## Coverage

The Makefile has a `coverage` target intended to produce Go coverage and open an HTML report:

```sh
make coverage
```

At present, the target writes `cover.out` but its second command refers to `coverage.out`. Treat that filename mismatch as a Makefile defect if using the target; the direct reliable commands are:

```sh
go test ./... -coverprofile=cover.out
go tool cover -html=cover.out
```

Documenting this mismatch is intentional so contributors do not assume a failing coverage target means the test suite itself failed.

## Debugging the example

The headless Delve target is:

```sh
make example-debug
```

Defaults:

```text
DEBUG_PORT=: 40000 (listen :40000)
EXAMPLE_ADDR=:8080 for normal example runs
```

The Makefile checks for Delve in `$(go env GOPATH)/bin/dlv` unless `DLV` is overridden.

## Common change paths

### Adding a new server-to-browser operation

1. Add or extend the Go dispatch payload in `dispatch_payloads.go`.
2. Add public `FnComponent`/helper behavior where appropriate in `component.go` or `view.go`.
3. Mirror the shape in `static/assets/neith_types.ts`.
4. Implement browser behavior in `render.ts` / `api.ts` or a focused new module.
5. Add Go tests for dispatch construction.
6. Add browser tests for resulting behavior.
7. Rebuild `neith.min.js`.
8. Update protocol/usage documentation and Grapher.

### Adding a DOM event payload

1. Confirm/add the event constant in `event_listener.go`.
2. Define/extend the Go payload type in `event_types.go` if a typed public struct is useful.
3. Serialize the event in `static/assets/event_payloads.ts`.
4. Confirm listener wiring in `events.ts`.
5. Add Go decode tests and browser serialization tests.
6. Update docs and Grapher relationships.

### Changing session/cache behavior

Treat `runtime.go`, `session.go`, `conn.go`, `cache.go`, and their tests as one subsystem. Reconnect behavior in `static/assets/socket.ts` is the browser half of the same lifecycle. Verify that stale sockets cannot write, reconnects preserve expected state, and inactive sessions still clean up.

### Changing uploads

Coordinate `upload.go`, `events.go`, `event_types.go`, `static/assets/uploads.ts`, event serialization, and tests. Preserve the design choice that file bytes travel over multipart HTTP and only metadata travels in event dispatch JSON unless deliberately redesigning the protocol.

## Formatting and generated-file discipline

Before committing Go changes:

```sh
gofmt -w <changed .go files>
go test ./...
```

Before committing browser-source changes:

```sh
cd static/assets
npm test
```

Rebuild the minified bundle whenever behavior shipped in TypeScript changes. A source-only TypeScript change without an updated embedded bundle means package consumers using embedded assets will still receive old browser behavior.

Likewise, changes to `dashboard.templ` should regenerate `dashboard_templ.go`.

## Grapher workflow

The project knowledge graph is shared under `.grapher/shared/`. Install/synchronize Grapher before doing graph-aware work:

```sh
pip install 'git+https://github.com/seanbman/grapher.git@main'
grapher sync
grapher search "dispatch browser protocol" --mode lexical
```

After meaningful code, test, or documentation changes, update the relevant semantic nodes and relationships rather than adding path-only stubs. Before publishing graph changes:

```sh
grapher scan .
grapher validate
grapher audit
grapher publish
```

A complete scan should have no pending recognized files. Repository-level coverage should also include tracked files whose extensions Grapher's default ingest classifier skips (for example extensionless build/license files and generated/template artifacts); the initial Neith index includes these explicitly.

## Release flow

The Makefile release target uses:

```sh
make publish VERSION=<version>
```

It creates an annotated `v<version>` tag, pushes it, asks the public Go proxy for the module version, and then queries the Go checksum database.

The Makefile currently defaults `VERSION ?= 0.4.11`; verify the intended release version before invoking `publish`.

### Pre-release checklist

1. `go test ./...` passes.
2. `npm test` passes in `static/assets`.
3. Generated browser and templ artifacts match their sources.
4. Root README and `docs/` describe the current public API.
5. Grapher has no pending indexed files and validates/audits cleanly.
6. The requested version/tag is intentional and not already present.
7. `go list -m github.com/seanbman/neith@vX.Y.Z` succeeds after the tag is pushed.

## Known maintenance edges

The current repository contains a few historical/build artifacts that should not be mistaken for primary source:

- minified JavaScript and CSS;
- generated `dashboard_templ.go`;
- largely empty Sass/CSS placeholder files;
- image-comment metadata under `static/.comments`.

The browser `package.json` version and Makefile's Go release version are independent metadata today. Unless a future release process explicitly couples them, do not infer the module tag from the npm package version.