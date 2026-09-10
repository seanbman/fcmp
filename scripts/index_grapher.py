#!/usr/bin/env python3
"""Build a complete semantic Grapher index for the Neith repository.

This script intentionally uses the public Grapher CLI from seanbman/grapher
rather than writing .grapher JSON directly. It starts from a clean local graph,
ingests every file type Grapher recognizes, enriches every pending stub, adds
explicit nodes for meaningful tracked files the default classifier skips, links
files into architectural subsystems, validates coverage, and publishes the
shareable graph.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
GRAPH_DIR = ROOT / ".grapher"
GRAPH_PATH = GRAPH_DIR / "knowledge.json"

DOC_EXTS = {
    ".md", ".txt", ".rst", ".pdf", ".doc", ".docx", ".rtf", ".csv", ".tsv",
    ".json", ".yaml", ".yml", ".toml", ".xml", ".html", ".htm", ".py", ".js",
    ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".c", ".h", ".cpp", ".hpp",
    ".cs", ".rb", ".php", ".sh", ".bash", ".zsh", ".sql", ".proto", ".graphql",
    ".css", ".scss", ".vue", ".svelte", ".ipynb",
}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg", ".ico", ".tif", ".tiff"}
VIDEO_EXTS = {".mp4", ".mov", ".webm", ".mkv", ".avi", ".m4v", ".wmv", ".flv"}
AUDIO_EXTS = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".wma", ".opus", ".aiff"}

# These summaries are deliberately semantic rather than path descriptions. Core
# implementation files explain behavior and ownership; tests explain the contract
# they verify; generated artifacts name their source and role.
SUMMARIES: dict[str, str] = {
    ".gitignore": "Repository ignore policy for local, editor, dependency, coverage, and generated working artifacts that should not become Neith source history.",
    ".github/workflows/grapher-index.yml": "GitHub Actions workflow that installs the canonical seanbman/grapher CLI, executes scripts/index_grapher.py, and commits the published shared semantic index back to this documentation branch. The generated-commit guard prevents the publish commit from recursively rerunning the indexing job.",
    ".vscode/launch.json": "VS Code launch configuration supporting local Neith development and debugging; editor-only configuration rather than runtime package behavior.",
    ".vscode/settings.json": "Repository-local VS Code settings used by contributors; editor configuration with no effect on the Neith wire protocol or package runtime.",
    "AGENTS.md": "Repository operating guidance for coding agents. It makes Grapher synchronization/search/update part of normal work, records Neith architectural invariants, identifies generated files, and requires Go/browser verification plus documentation alignment.",
    "LICENSE": "Canonical repository license text governing distribution and reuse of Neith source code and artifacts.",
    "Makefile": "Developer and release command surface. It runs Go and browser tests, the runnable example and Delve debugging, templ generation, TypeScript/esbuild/Tailwind/Sass asset builds, coverage, and tagged Go-module publication. The current coverage target contains a cover.out versus coverage.out filename mismatch documented in docs/DEVELOPMENT.md.",
    "README.md": "Public package overview and broad API guide. It introduces Neith as a Go server-rendered interactive component layer, documents installation and quick start, explains App/View/FnComponent layers, events, DOM effects, per-client cache, configuration, optional UI components, and the example application.",
    "cache.go": "Implements generic Cache[T] state scoped to one browser client inside one Neith runtime. It owns cache creation/type checks, Set/Value/Delete, timestamps and expiry, stale-watcher protection, optional history, change/timeout callbacks, runtime-wide callback registry, and per-client cache stores guarded by mutexes.",
    "cache_test.go": "Verifies typed cache creation and retrieval, duplicate and wrong-type behavior, mutation, timeout/expiry semantics, history and callbacks, cleanup, and isolation assumptions that make Cache[T] safe as per-client Neith state.",
    "component.go": "Defines Neith's minimal Component interface and the central FnComponent dispatch wrapper. It renders components into a buffered server-side wrapper, copies active runtime/session context, attaches browser events, selects tag/element render modes, supports redirect/error/custom JavaScript dispatch, immediate Dispatch, class and focused DOM helpers, removals, and raw HTML adaptation.",
    "component_test.go": "Tests Component/FnComponent rendering, wrapper metadata, target/mode selection, event wiring metadata, dispatch behavior, and convenience effects so public component APIs remain aligned with the dispatch protocol.",
    "conn.go": "Owns one Gorilla WebSocket transport for a Neith client session. It upgrades HTTP, attaches the connection to the runtime session registry, closes superseded sockets, decodes inbound Dispatch messages, serializes outbound messages, rejects writes from stale connections, and schedules inactive-session/cache cleanup after CacheTimeOut.",
    "conn_test.go": "Exercises WebSocket connection/session lifecycle and publication behavior, especially the active-connection rule that prevents a superseded socket from writing after a reconnect.",
    "context.go": "Defines Neith context keys plus internal dispatchDetails carrying runtime, client ID, connection, and handler ID. These context values bind application handlers and FnComponents to the correct mounted runtime and browser session.",
    "dispatch.go": "Defines the JSON WebSocket Dispatch envelope and operation selector used by both server and browser. It carries render, ping, class, DOM, redirect, event, custom-JavaScript, and error payloads and serializes event-listener metadata for rendered wrappers.",
    "dispatch_payloads.go": "Defines Go payload structs for each server/browser dispatch operation: rendering target/mode/HTML/listeners, ping liveness, class changes, focused DOM operations, redirects, custom JavaScript calls/results, and protocol errors.",
    "dispatch_test.go": "Verifies dispatch initialization, operation/payload state, and message-shape assumptions that must stay synchronized with static/assets/neith_types.ts.",
    "errors.go": "Exports stable error values for missing Neith dispatch/event context, absent or failed client connections, and typed cache not-found/store/wrong-type/duplicate conditions.",
    "event_listener.go": "Defines the supported DOM event-name constants, EventListener metadata, and the runtime/client-scoped event listener registry. Listener registration binds a Go HandleFn to a generated listener ID that the browser echoes in event dispatches.",
    "event_types.go": "Defines exported JSON-safe event payloads shared with application handlers: Upload metadata, DOM EventTarget snapshots, pointer/mouse/keyboard/drag/touch data, and form-data event shapes.",
    "events.go": "Handler-facing event accessors. EventData[T] decodes the current browser payload into an application-selected type, EventUploads returns metadata from prior multipart file uploads, and EventSubmitter exposes the control that submitted a form.",
    "events_test.go": "Verifies event payload decoding, missing-event context errors, submitter metadata, and upload metadata access from handler contexts.",
    "go.mod": "Canonical Go module manifest declaring module github.com/seanbman/neith, Go 1.21.5, and the transport/logging/UUID dependency set used by the server package.",
    "go.sum": "Go module checksum lock data ensuring reproducible integrity for Neith's direct and transitive Go dependencies; derived dependency metadata rather than application logic.",
    "handler.go": "Implements each mounted runtime's handler pool and bidirectional dispatch pipeline. Incoming WebSocket operations are routed to ping/event/custom/error handling; outgoing FnComponents are routed to render/class/DOM/redirect/custom/error publishing. MiddleWareFn creates an isolated runtime per mount, serves normal HTTP/upload/WebSocket flows, injects dispatch context, sends the initial view, and starts liveness pings.",
    "page.go": "Implements the default server-generated HTML Page and App mounting helper. It provides page options for title/language/target/classes/assets/head/body, embeds neith.min.js and neith-ui.css with go:embed, serves those embedded assets, and delegates interactive requests to MiddleWareFn.",
    "page_test.go": "Tests default and customized Page output, App shell behavior, page-option composition, and serving of the two embedded Neith browser/UI assets.",
    "pkg.go": "Package configuration root. It defines log levels, global/default Config, defaults of 30-minute cache timeout, Error logging, 64 MiB upload body and 32 MiB multipart memory, logger initialization, and SetConfig propagation into the default runtime.",
    "runtime.go": "Defines the internal Neith runtime ownership boundary. A runtime groups its own handler pool, client sessions, event listeners, per-client cache stores, cache callbacks/history, and configuration; each MiddleWareFn/App mount creates one isolated runtime.",
    "runtime_test.go": "Tests runtime construction/configuration and the isolation assumptions used to keep separate mounted Neith apps from sharing handler/session/cache/listener state.",
    "session.go": "Implements clientSession and its registry. A stable browser client ID can survive WebSocket replacement; Attach installs one active connection and returns the prior one, Detach only clears the matching connection, and inactive sessions can be deleted after timeout.",
    "session_test.go": "Verifies session attach, active-connection replacement, detach semantics, lookup, and inactive deletion behavior used by reconnection and cache retention.",
    "tailwind.config.js": "Tailwind build configuration for the repository's optional/generated stylesheet pipeline. It is build-time styling metadata and separate from the neutral neith-ui.css embedded by page.go.",
    "upload.go": "Implements Neith's multipart HTTP upload endpoint used before WebSocket event dispatch. It enforces configurable body/memory limits, creates a private upload directory, strips client path components, stores UUID-prefixed files with restrictive permissions, and returns Upload metadata; successful file retention/deletion remains the host application's responsibility.",
    "upload_test.go": "Tests multipart upload method handling, persistence, metadata, directory selection, size/memory behavior, and related safeguards in upload.go.",
    "utils.go": "Small internal utility helpers shared by Neith implementation code; supporting mechanics rather than a standalone public subsystem.",
    "view.go": "High-level readable application API over FnComponent. View applies composable options for common DOM events, labels, and tag/element append/prepend/inner/outer render targeting while preserving the same underlying dispatch model as NewFn.",
    "view_test.go": "Confirms View and ViewOption helpers map correctly onto lower-level FnComponent event and render-target behavior.",
    "ui/component.go": "Optional renderer-agnostic UI package built on neith.Component. It provides semantic layout, headings, forms, controls, selects, tables and alerts plus attribute/class/label/choice/state options, with HTML escaping and deterministic attribute rendering; it can be mixed with templ and custom components.",
    "ui/component_test.go": "Tests optional UI component rendering, escaping, attributes/classes, labels, form controls, choice handling, tables, and composition into normal Neith components.",
    "notes/README.md": "Entry point for the repository's focused implementation notes, directing maintainers to detailed component and cache references.",
    "notes/cache/README.md": "Detailed Cache[T] reference covering per-client/runtime scope, NewCache/UseCache, Set timeout rules, timestamps, deletion, history recording, callbacks, errors, and the internal store/expiry flow.",
    "notes/component/README.md": "Detailed Component/FnComponent reference covering rendering, context, event attachment, redirects/errors/custom JavaScript, render targets, immediate Dispatch, helper effects, and the internal dispatch flow.",
    "examples/readme-setup/README.md": "Consumer-oriented documentation for the runnable example, showing how an external-style Go module sets up and runs a Neith application.",
    "examples/readme-setup/dashboard.templ": "Source templ component for the runnable example dashboard. It is the human-edited template whose generated Go implementation is dashboard_templ.go.",
    "examples/readme-setup/dashboard_templ.go": "Generated Go code produced from dashboard.templ for the runnable example. It is build output used at compile time and should be regenerated from the templ source rather than edited directly.",
    "examples/readme-setup/go.mod": "Standalone example module manifest, intentionally modeling how a consumer depends on Neith and templ rather than relying on unexported repository internals.",
    "examples/readme-setup/go.sum": "Dependency checksum data for the standalone readme-setup example module.",
    "examples/readme-setup/main.go": "Runnable HTTP example demonstrating public Neith application mounting and interaction APIs in a consumer-style module.",
    "examples/readme-setup/static/example.css": "Example-only stylesheet used to present the runnable readme-setup application; not part of the package's neutral embedded UI stylesheet.",
    "static/.comments/logo.png.xml": "Metadata sidecar associated with static/logo.png. Its caption, note, place, and categories fields are currently empty, so it contributes no runtime behavior or additional brand semantics.",
    "static/favicon.ico": "Tracked browser favicon branding artifact for Neith/static page contexts. It is a visual project identity asset and is not part of the Go dispatch protocol.",
    "static/icon.png": "Tracked Neith icon branding image used alongside static application assets. It is a visual identity artifact distinct from the README logo and is not among page.go's two embedded runtime assets.",
    "static/index.html": "Historical/static HTML shell artifact under the repository's static tree. Current Neith App behavior generates its normal page shell programmatically through page.go rather than relying on this file.",
    "static/logo.png": "Primary tracked Neith project logo/branding image referenced by the root README. It provides visual identity for the package and is non-executable repository content.",
    "static/manifest.json": "Static browser manifest metadata associated with Neith's web assets/branding; auxiliary application metadata rather than the interactive server/browser protocol.",
    "static/assets/api.ts": "Browser-side dispatch router. API.Process receives Go Dispatch messages, handles redirect directly, maps ping/render/class/DOM/custom operations to browser effects, sends response dispatches when needed, and converts client-side protocol failures into error dispatches plus lifecycle hooks.",
    "static/assets/custom.js": "Small browser-side custom JavaScript/example fixture used with Neith's custom function dispatch escape hatch; auxiliary client code rather than the core TypeScript runtime.",
    "static/assets/event_payloads.ts": "Serializes native browser events and DOM targets into JSON-safe payload structures that correspond to Go event_types.go, including event-specific coordinates/modifiers and source/component target snapshots.",
    "static/assets/events.ts": "Browser event bridge. It parses listener metadata emitted in server-rendered wrappers, attaches native DOM listeners, builds event dispatches, coordinates form/file handling, and emits before/after event-dispatch lifecycle hooks.",
    "static/assets/hooks.ts": "Client lifecycle hook registry and public window.neith API. It supports connect/disconnect/reconnect, render, event-dispatch, and error hooks with on/off registration and an unsubscribe function.",
    "static/assets/index.ts": "Browser bundle entrypoint. Importing it constructs a Socket immediately so the compiled neith.min.js connects back to the Neith server and starts client dispatch processing.",
    "static/assets/jest.config.js": "Jest/ts-jest/jsdom configuration for executing the TypeScript browser-runtime integration suite in a DOM-like test environment.",
    "static/assets/neith-ui.css": "Neutral stylesheet shipped for Neith's optional ui package and embedded by page.go at /assets/neith-ui.css. Applications can override its CSS variables or add their own styles without changing the component protocol.",
    "static/assets/neith.min.js": "Generated minified browser bundle produced from static/assets/index.ts and its TypeScript dependency graph by esbuild. page.go embeds this derived artifact so package consumers receive the browser runtime; behavioral edits belong in TypeScript source, followed by a rebuild.",
    "static/assets/neith_types.ts": "TypeScript mirror of Neith's Go Dispatch envelope, function names, operation payloads, event metadata, and upload types. It is the browser half of the wire contract and must change in lockstep with dispatch.go, dispatch_payloads.go, and event types.",
    "static/assets/package.json": "Browser-development package metadata. It defines the Jest coverage test command and TypeScript/jsdom/websocket-mock development dependencies used to verify the client runtime; its package version is independent of the Go module release tag today.",
    "static/assets/render.ts": "Concrete browser DOM-effect implementation invoked by api.ts: applying server-rendered HTML by target/mode, class changes, focused DOM operations, and custom global JavaScript calls while reporting invalid targets/operations through the protocol error path.",
    "static/assets/sass/styles.sass": "Current Sass source/placeholder entry for the optional style build. It is separate from the embedded neutral neith-ui.css and is compiled through the Makefile Sass target when populated.",
    "static/assets/socket.ts": "Browser WebSocket lifecycle owner. It derives a same-route ws/wss URL, persists a stable neith client key in localStorage, creates API per connection, emits connect/disconnect/reconnect hooks, and retries unexpected disconnects with capped exponential backoff from 500 ms to 30 seconds.",
    "static/assets/stylesheets/styles.css": "Compiled or placeholder stylesheet output associated with the Sass build surface; derived presentation material rather than the authoritative Neith UI/dispatch implementation.",
    "static/assets/stylesheets/styles.css.map": "Generated source-map metadata for styles.css, linking compiled CSS back to its style source during debugging; build artifact rather than editable behavior.",
    "static/assets/stylesheets/tailwind.css": "Tailwind source/input stylesheet used by the Makefile Tailwind build target.",
    "static/assets/stylesheets/tailwind.min.css": "Generated minified Tailwind stylesheet produced from tailwind.css by the repository's Tailwind build target; edit the source/config rather than this derived output.",
    "static/assets/tests/index.test.ts": "Browser integration suite using Jest/jsdom and WebSocket mocks to verify dispatch routing, DOM rendering/mutations, event serialization, uploads, hooks, errors, ping replies, and reconnection behavior from the client runtime's observable contract.",
    "static/assets/tsconfig.json": "TypeScript compiler configuration for Neith's browser-client source and development/test toolchain.",
    "static/assets/uploads.ts": "Browser form/upload transport helper. It separates normal form values from files, preserves submitter name/value including a compatibility fallback, uploads selected files by multipart HTTP to neith_upload=1 with the stable client ID, and returns server Upload metadata for the later event dispatch.",
    "docs/README.md": "Maintainer/user documentation index defining the mental model, source-of-truth order, generated-file rules, focused legacy references, and the expected Grapher search/sync/validate/audit workflow.",
    "docs/ARCHITECTURE.md": "Comprehensive cross-runtime architecture reference with Mermaid diagrams for App/Page mounting, isolated runtimes, client sessions versus WebSockets, handler channels, render targeting, dispatch protocol, event/upload/cache flows, browser modules, generated assets, concurrency, and security boundaries.",
    "docs/USAGE.md": "Comprehensive current-source usage guide covering installation, minimal App/View setup, rendering and targets, events, uploads, generic cache, page/config options, DOM effects, redirects/custom JavaScript, optional ui components, multiple routes, production cautions, and exported errors.",
    "docs/BROWSER_CLIENT.md": "Focused TypeScript browser-runtime documentation covering module ownership, startup, same-route WebSocket and reconnect lifecycle, server-to-browser dispatch, DOM/event/form/upload behavior, lifecycle hooks, error propagation, type-contract synchronization, build, and tests.",
    "docs/DEVELOPMENT.md": "Contributor workflow for toolchain setup, Go/browser test suites, example and templ generation, browser/style asset builds, debugging, common subsystem change paths, generated-file discipline, Grapher maintenance, release procedure, and known build-maintenance edges.",
    "docs/REPOSITORY_MAP.md": "File-by-file repository ownership map distinguishing core Go source, tests, ui package, TypeScript runtime, style/generated assets, branding, example, notes, editor configuration, documentation, and Grapher artifacts, plus a subsystem relationship diagram.",
    "scripts/index_grapher.py": "Reproducible semantic-index builder for Neith. It invokes the canonical Grapher CLI, enriches every recognized tracked file, explicitly indexes tracked files Grapher's default classifier skips, links files to architectural concepts, checks complete path coverage/pending state, validates/audits/searches the graph, and publishes shared graph state.",
}

CONCEPTS: dict[str, tuple[str, str]] = {
    "neith-system": ("Neith system", "Neith is a Go-first server-rendered interactive component system. Go owns rendering, event handlers, state and the authoritative dispatch protocol; a thin TypeScript browser runtime owns WebSocket transport, DOM effects, event capture, uploads and lifecycle hooks."),
    "app-page-shell": ("App and page shell", "App/NewPage/Page generate the HTTP document, expose page customization, embed the browser bundle and neutral UI stylesheet, and hand interactive traffic to a dedicated MiddleWareFn runtime for each mount."),
    "server-runtime": ("Server runtime and sessions", "Each mounted Neith app owns an isolated runtime containing handlers, client sessions, event listeners, cache stores and config. A stable browser client ID may survive WebSocket replacement while only one connection remains active at a time."),
    "component-rendering": ("Component and rendering model", "The Component interface is the server-rendered unit. View and FnComponent wrap rendered HTML with event and render-target instructions so Go can append, prepend, swap or remove browser regions without adopting a client-side component framework."),
    "dispatch-protocol": ("Dispatch protocol", "Dispatch and its nested payloads form the JSON WebSocket contract between Go and TypeScript for ping, render, class, DOM, redirect, event, custom JavaScript and error operations."),
    "event-system": ("Event system", "Server-rendered wrappers carry listener metadata. The browser binds native events, serializes JSON-safe payloads and listener identity, and Go resolves the handler in the current runtime/client scope before invoking it with EventKey context."),
    "upload-system": ("Upload system", "Selected file bytes travel by multipart HTTP before the event WebSocket dispatch; the server persists files under configured limits and returns Upload metadata that the browser attaches to the event for EventUploads."),
    "cache-system": ("Session cache system", "Cache[T] provides typed per-client state inside one mounted runtime, with duplicate/type checks, configurable expiry, stale-watcher protection, optional history, and change/timeout callbacks."),
    "browser-runtime": ("Browser runtime", "The TypeScript client creates a same-route WebSocket, maintains a stable localStorage client key, reconnects unexpected transport failures, applies dispatches to the DOM, serializes browser events, coordinates uploads, and exposes lifecycle hooks."),
    "ui-package": ("Optional UI package", "The ui package supplies small renderer-agnostic neith.Component primitives for layouts, forms, controls, tables and alerts. It is optional and composes with templ or custom renderers rather than defining another runtime."),
    "example-consumer": ("Runnable consumer example", "examples/readme-setup is a consumer-style Go module showing Neith with templ and local styling, including generated templ output and a runnable HTTP server."),
    "build-release": ("Build, test and release workflow", "The repository uses Go tests plus Jest/jsdom browser tests, templ generation, TypeScript/esbuild bundling, Tailwind/Sass asset tasks, Delve debugging and tagged Go-module publication. Generated artifacts must stay synchronized with their editable sources."),
    "documentation": ("Repository documentation", "The root README is the public overview while docs/ separates architecture, usage, browser-client, development, and repository-map concerns; focused notes retain detailed component/cache references and AGENTS.md makes this documentation plus Grapher part of ongoing maintenance."),
    "static-branding": ("Static branding and web metadata", "Tracked logo, icon, favicon, manifest, historical static shell and image metadata provide project/browser identity or historical static context. They are separate from the two runtime assets embedded by page.go."),
}

CONCEPT_LINKS = [
    ("app-page-shell", "neith-system", "part_of"),
    ("server-runtime", "neith-system", "part_of"),
    ("component-rendering", "neith-system", "part_of"),
    ("dispatch-protocol", "neith-system", "part_of"),
    ("event-system", "neith-system", "part_of"),
    ("upload-system", "event-system", "part_of"),
    ("cache-system", "server-runtime", "part_of"),
    ("browser-runtime", "neith-system", "part_of"),
    ("browser-runtime", "dispatch-protocol", "depends_on"),
    ("event-system", "dispatch-protocol", "depends_on"),
    ("server-runtime", "dispatch-protocol", "depends_on"),
    ("ui-package", "component-rendering", "depends_on"),
    ("example-consumer", "neith-system", "implements"),
    ("build-release", "neith-system", "maintains"),
    ("documentation", "neith-system", "references"),
    ("static-branding", "neith-system", "part_of"),
]


def run(args: list[str], *, capture: bool = False) -> str:
    cmd = ["grapher", *args]
    print("+", " ".join(cmd), flush=True)
    completed = subprocess.run(
        cmd,
        cwd=ROOT,
        env=os.environ.copy(),
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
        check=False,
    )
    if completed.returncode != 0:
        if capture:
            sys.stderr.write(completed.stdout or "")
            sys.stderr.write(completed.stderr or "")
        raise SystemExit(f"command failed ({completed.returncode}): {' '.join(cmd)}")
    return completed.stdout if capture else ""


def tracked_files() -> list[str]:
    output = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True)
    return sorted(
        p for p in output.splitlines()
        if p and not p.startswith(".grapher/")
    )


def classify(path: str) -> str | None:
    ext = Path(path).suffix.lower()
    if ext in DOC_EXTS:
        return "document"
    if ext in IMAGE_EXTS:
        return "image"
    if ext in VIDEO_EXTS:
        return "video"
    if ext in AUDIO_EXTS:
        return "audio"
    return None


def stable_path_id(path: str, node_type: str) -> str:
    digest = hashlib.sha1(path.encode("utf-8")).hexdigest()[:10]
    stem = Path(path).stem.lower()
    stem = "".join(ch if ch.isalnum() else "-" for ch in stem)
    stem = "-".join(part for part in stem.split("-") if part)[:32] or "node"
    return f"{node_type}-{stem}-{digest}"


def tags_for(path: str) -> list[str]:
    tags = ["repo-index", "neith"]
    if path.endswith("_test.go") or path.endswith(".test.ts"):
        tags.append("test")
    if path.startswith("docs/") or path.startswith("notes/") or path == "README.md" or path == "AGENTS.md":
        tags.append("documentation")
    if path.startswith("static/assets/"):
        tags.append("browser" if path.endswith((".ts", ".js")) else "asset")
    if path.startswith("examples/"):
        tags.append("example")
    if path.startswith("ui/"):
        tags.append("ui")
    if path in {"static/assets/neith.min.js", "static/assets/stylesheets/tailwind.min.css", "static/assets/stylesheets/styles.css", "static/assets/stylesheets/styles.css.map", "examples/readme-setup/dashboard_templ.go", "go.sum", "examples/readme-setup/go.sum"}:
        tags.append("generated")
    if path.startswith("static/") and not path.startswith("static/assets/"):
        tags.append("static")
    return tags


def concept_for(path: str) -> str:
    name = Path(path).name
    if path.startswith("docs/") or path.startswith("notes/") or path in {"README.md", "AGENTS.md"}:
        return "documentation"
    if path.startswith("examples/"):
        return "example-consumer"
    if path.startswith("ui/"):
        return "ui-package"
    if path.startswith("static/") and not path.startswith("static/assets/"):
        return "static-branding"
    if path.startswith("static/assets/"):
        if name in {"uploads.ts"}:
            return "upload-system"
        if name in {"events.ts", "event_payloads.ts"}:
            return "event-system"
        if name in {"neith_types.ts"}:
            return "dispatch-protocol"
        if name in {"package.json", "tsconfig.json", "jest.config.js"} or path.startswith("static/assets/stylesheets/") or path.startswith("static/assets/sass/"):
            return "build-release"
        return "browser-runtime"
    if name.startswith("cache"):
        return "cache-system"
    if name.startswith("upload"):
        return "upload-system"
    if name.startswith("event") or name == "events.go" or name == "events_test.go":
        return "event-system"
    if name.startswith("dispatch"):
        return "dispatch-protocol"
    if name.startswith("component") or name.startswith("view"):
        return "component-rendering"
    if name.startswith("page") or name == "pkg.go":
        return "app-page-shell"
    if name.startswith("runtime") or name.startswith("session") or name.startswith("conn") or name.startswith("handler") or name == "context.go":
        return "server-runtime"
    if path in {"Makefile", "go.mod", "go.sum", "tailwind.config.js", ".gitignore", ".vscode/launch.json", ".vscode/settings.json", "LICENSE", "scripts/index_grapher.py", ".github/workflows/grapher-index.yml"}:
        return "build-release"
    return "neith-system"


def graph_json() -> dict:
    return json.loads(GRAPH_PATH.read_text(encoding="utf-8"))


def add_file_node(path: str, summary: str, recognized_type: str | None) -> str:
    if recognized_type:
        node_type = recognized_type
        node_id = stable_path_id(path, node_type)
        args = [
            "add", "--enrich-pending",
            "--id", node_id,
            "--type", node_type,
            "--title", Path(path).name,
            "--path", path,
            "--content", summary,
            "--tags", ",".join(tags_for(path)),
            "--stage", "maintaining",
            "--status", "current",
            "--workflow-state", "not_applicable",
            "--verification", "partially_verified",
            "--reason", f"Semantic enrichment of tracked repository file {path}",
        ]
    else:
        node_type = "artifact"
        node_id = stable_path_id(path, node_type)
        args = [
            "add",
            "--id", node_id,
            "--type", node_type,
            "--title", Path(path).name,
            "--path", path,
            "--content", summary,
            "--tags", ",".join(tags_for(path) + ["explicit-non-ingest-type"]),
            "--stage", "maintaining",
            "--status", "current",
            "--workflow-state", "not_applicable",
            "--verification", "partially_verified",
            "--reason", f"Explicit semantic index for tracked file skipped by Grapher ingest classifier: {path}",
        ]
    run(args)
    return node_id


def link(frm: str, to: str, rel: str, note: str) -> None:
    run(["link", frm, to, "--rel", rel, "--note", note, "--reason", note])


def ensure_exact_summary_coverage(paths: Iterable[str]) -> None:
    paths = list(paths)
    missing = sorted(set(paths) - set(SUMMARIES))
    stale = sorted(set(SUMMARIES) - set(paths))
    if missing or stale:
        details = []
        if missing:
            details.append("Missing semantic summaries:\n  " + "\n  ".join(missing))
        if stale:
            details.append("Summary entries for non-tracked paths:\n  " + "\n  ".join(stale))
        raise SystemExit("\n".join(details))


def verify_graph_coverage(paths: Iterable[str]) -> None:
    graph = graph_json()
    nodes = graph.get("nodes", {})
    indexed_paths = {node.get("path") for node in nodes.values() if node.get("path")}
    missing = sorted(set(paths) - indexed_paths)
    empty = sorted(
        node.get("path") or node_id
        for node_id, node in nodes.items()
        if node.get("path") in set(paths) and not str(node.get("content") or "").strip()
    )
    pending = sorted(
        node.get("path") or node_id
        for node_id, node in nodes.items()
        if (node.get("meta") or {}).get("status") == "pending"
    )
    if missing or empty or pending:
        raise SystemExit(json.dumps({"missing_paths": missing, "empty_content": empty, "pending_nodes": pending}, indent=2))


def main() -> None:
    os.environ.setdefault("GRAPHER_PROJECT_ID", "seanbman/neith")
    os.environ.setdefault("GRAPHER_WORKSPACE_ID", "github")
    os.environ.setdefault("GRAPHER_ACTOR_ID", "chatgpt-gpt-5.6-sol")
    os.environ.setdefault("GRAPHER_ACTOR_KIND", "agent")
    os.environ.setdefault("GRAPHER_ACTOR_ROLE", "repository-documentation-indexer")
    os.environ.setdefault("GRAPHER_SOURCE", "repository-index")

    paths = tracked_files()
    ensure_exact_summary_coverage(paths)

    # Build from a clean local store so the published graph is reproducible from
    # the current tracked tree rather than inheriting stale historical stubs.
    shutil.rmtree(GRAPH_DIR, ignore_errors=True)
    run(["init", "--profile", "software", "--name", "neith", "--all-stages"])
    run(["ingest", ".", "--max-files", "5000", "--reason", "Full tracked Neith repository ingest before semantic enrichment"])

    file_nodes: dict[str, str] = {}
    for path in paths:
        file_nodes[path] = add_file_node(path, SUMMARIES[path], classify(path))

    # Add architectural concepts after the file ingest. These are semantic
    # navigation anchors rather than substitutes for file-level understanding.
    for node_id, (title, content) in CONCEPTS.items():
        run([
            "add",
            "--id", node_id,
            "--type", "concept",
            "--title", title,
            "--content", content,
            "--tags", "repo-index,architecture,neith",
            "--stage", "maintaining",
            "--status", "current",
            "--workflow-state", "not_applicable",
            "--verification", "partially_verified",
            "--reason", f"Architectural navigation concept: {title}",
        ])

    for path, node_id in file_nodes.items():
        concept = concept_for(path)
        relation = "references" if "documentation" in tags_for(path) else "part_of"
        link(node_id, concept, relation, f"{path} belongs to or documents the {CONCEPTS[concept][0]} subsystem")

    for frm, to, rel in CONCEPT_LINKS:
        link(frm, to, rel, f"Architectural relationship: {CONCEPTS[frm][0]} {rel} {CONCEPTS[to][0]}")

    verify_graph_coverage(paths)

    scan = json.loads(run(["scan", ".", "--max-files", "5000", "--json"], capture=True))
    counts = scan.get("counts", {})
    if counts.get("pending", 0) != 0 or counts.get("new", 0) != 0:
        raise SystemExit("Grapher scan incomplete: " + json.dumps(counts, sort_keys=True))

    validate = json.loads(run(["validate", "--json"], capture=True))
    audit = json.loads(run(["audit", "--json"], capture=True))
    search = json.loads(run([
        "search", "WebSocket reconnect session cache dispatch browser runtime",
        "--mode", "lexical", "--json",
    ], capture=True))

    # A semantic index must prove useful retrieval, not only structural validity.
    result_count = len(search) if isinstance(search, list) else len(search.get("results", []))
    if result_count == 0:
        raise SystemExit("Grapher lexical retrieval check returned no results")

    publish = json.loads(run(["publish", "--json"], capture=True))

    report = {
        "tracked_files": len(paths),
        "recognized_ingest_files": sum(1 for p in paths if classify(p)),
        "explicit_non_ingest_files": sum(1 for p in paths if not classify(p)),
        "concept_nodes": len(CONCEPTS),
        "scan_counts": counts,
        "search_result_count": result_count,
        "validate": validate,
        "audit": audit,
        "publish": publish,
    }
    print("\nNEITH GRAPHER INDEX COMPLETE")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
