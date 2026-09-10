# Usage Guide

This guide describes the current source behavior of Neith. For internals, see [`ARCHITECTURE.md`](ARCHITECTURE.md); for the browser runtime, see [`BROWSER_CLIENT.md`](BROWSER_CLIENT.md).

## Requirements and installation

Neith's module declares Go `1.21.5` and uses Gorilla WebSocket for transport. Install the package with:

```sh
go get github.com/seanbman/neith
```

For a root-mounted application, `neith.App` can serve the embedded `/assets/neith.min.js` and `/assets/neith-ui.css` files itself. If you mount Neith only under a nested route or prefer to own static delivery, copy the browser bundle into your own static directory and set `ClientScript` to that URL.

## Smallest useful application

```go
package main

import (
    "context"
    "log"
    "net/http"

    "github.com/seanbman/neith"
)

func home(ctx context.Context) neith.FnComponent {
    return neith.View(ctx,
        neith.HTML(`<button id="hello">Say hello</button>`),
        neith.OnClick(hello),
    )
}

func hello(ctx context.Context) neith.FnComponent {
    return neith.View(ctx,
        neith.HTML(`<h1>Hello from Go</h1>`),
        neith.IntoTag("main"),
    )
}

func main() {
    http.HandleFunc("/", neith.App(home, neith.Title("Neith demo")))
    log.Fatal(http.ListenAndServe(":8080", nil))
}
```

The first normal HTTP request receives a page containing a `<main>` render target. The browser script creates a stable `neith_id`, opens a WebSocket back to the route, and the server sends the initial `FnComponent`. Subsequent matching DOM events call Go handlers over the same dispatch protocol.

## Rendering values

Anything implementing the following interface is a Neith component:

```go
type Component interface {
    Render(ctx context.Context, w io.Writer) error
}
```

That includes `templ` output, `neith.HTML`, components from `github.com/seanbman/neith/ui`, and custom types.

Raw HTML is convenient for small fragments:

```go
return neith.View(ctx, neith.HTML(`<p>Saved</p>`))
```

Use `RenderComponent` when you want a plain string without a live browser connection:

```go
html := neith.RenderComponent(
    neith.HTML(`<h1>Report</h1>`),
    neith.HTML(`<p>Complete</p>`),
)
```

## Prefer `View` for application code

`View` is the readable application layer over `FnComponent`:

```go
return neith.View(ctx, dashboard(rows),
    neith.Label("dashboard"),
    neith.OnSubmit(save),
    neith.IntoElement("content"),
)
```

Common event helpers are:

```go
neith.OnClick(handler)
neith.OnSubmit(handler)
neith.OnChange(handler)
neith.OnInput(handler)
neith.OnKeyDown(handler)
neith.On(neith.EventPointerDown, handler)
```

Aliases `Click`, `Submit`, `Change`, `Input`, and `KeyDown` are also available.

### Render targets

`NewFn` and therefore `View` default to replacing the inner HTML of the first `<main>` element. Override that behavior with one target option:

```go
neith.IntoTag("main")
neith.IntoElement("content")
neith.AppendToTag("ul")
neith.PrependToTag("main")
neith.AppendToElement("items")
neith.PrependToElement("messages")
neith.SwapTagInner("main")
neith.SwapTagOuter("main")
neith.SwapElementInner("panel")
neith.SwapElementOuter("card")
```

Use inner swaps when the target element should survive, outer swaps when the rendered value replaces the target itself, and append/prepend when preserving existing children.

## Lower-level `FnComponent`

Use `NewFn` when building abstractions, tests, or code that needs to control dispatch explicitly:

```go
return neith.NewFn(ctx, dashboard(rows)).
    WithLabel("dashboard").
    WithEvents(save, neith.EventSubmit).
    SwapTagInner("main")
```

A returned `FnComponent` is normally sent after the event handler finishes. `Dispatch()` sends it immediately and is useful for secondary side effects:

```go
neith.NewFn(ctx, neith.HTML(`<p>Queued</p>`)).
    AppendElement("notifications").
    Dispatch()

return neith.View(ctx, updatedPage())
```

`Dispatch()` requires a context created by Neith middleware and an active client connection.

## Page configuration

`neith.App` constructs a default `Page`. Customize it using page options:

```go
http.HandleFunc("/", neith.App(home,
    neith.Title("Admin"),
    neith.Lang("en"),
    neith.Target("main", "app"),
    neith.BodyClass("app-shell"),
    neith.TargetClass("app-content"),
    neith.Stylesheet("/static/app.css"),
    neith.Script("/static/app.js"),
    neith.Head(neith.HTML(`<meta name="theme-color" content="#111">`)),
    neith.Style(`:root { color-scheme: dark; }`),
))
```

`ClientScript(url)` replaces the default script list with the supplied browser-client URL. Use it when serving your own copy of `neith.min.js`:

```go
http.HandleFunc("/console/", neith.App(home,
    neith.ClientScript("/static/assets/neith.min.js"),
))
```

If you need to build the page yourself, `NewPage` returns a renderable `Page` and `MiddleWareFn(page.ServeHTTP, appFn)` exposes the lower-level middleware form.

## Event data

Handlers receive a `context.Context` containing the current `EventListener`. Decode its browser payload using `EventData[T]`:

```go
func save(ctx context.Context) neith.FnComponent {
    values, err := neith.EventData[map[string]string](ctx)
    if err != nil {
        return neith.FnErr(ctx, err)
    }

    return neith.View(ctx,
        neith.HTML(`<p>Saved `+html.EscapeString(values["name"])+`</p>`),
        neith.IntoElement("status"),
    )
}
```

For richer browser events, decode into Neith's matching structs such as `PointerEvent`, `MouseEvent`, `KeyboardEvent`, `DragEvent`, `TouchEvent`, or `FormDataEvent`.

`EventTarget` snapshots can include ID, name, class list, tag name, inner/outer HTML, value, checked/disabled/hidden state, inline style, attributes, dataset, and selected options.

For form submission, inspect the actual submit button/input:

```go
submitter, err := neith.EventSubmitter(ctx)
if err != nil {
    return neith.FnErr(ctx, err)
}
if submitter != nil && submitter.Value == "delete" {
    // destructive action selected
}
```

## File uploads

When a form event includes file inputs, the browser uploads file bytes by multipart HTTP before sending the event dispatch. Read the resulting metadata in Go:

```go
uploads, err := neith.EventUploads(ctx)
if err != nil {
    return neith.FnErr(ctx, err)
}
for _, upload := range uploads {
    log.Printf("%s -> %s (%d bytes)", upload.FileName, upload.Path, upload.Size)
}
```

Each `Upload` contains `ID`, `FieldName`, `FileName`, `ContentType`, `Size`, and server `Path`.

Configure limits and destination using `Config`:

```go
cfg := &neith.Config{
    CacheTimeOut:    30 * time.Minute,
    LogLevel:        neith.Info,
    UploadDir:       "/srv/myapp/uploads",
    UploadMaxBytes:  32 << 20,
    UploadMaxMemory: 8 << 20,
}
neith.SetConfig(cfg)
```

If values are non-positive, upload handling falls back to 64 MiB maximum request size and 32 MiB multipart memory. When `UploadDir` is empty, files are stored under the process temporary directory in `neith-uploads`.

Neith does not delete successful uploads automatically. Treat `Upload.Path` as application-owned temporary/persistent data and implement validation, retention, and deletion appropriate to the host app.

## Session-scoped cache

Caches are generic and scoped to the current client session inside the current mounted runtime.

```go
func app(ctx context.Context) neith.FnComponent {
    _, err := neith.NewCache(ctx, "count", 0)
    if err != nil && !errors.Is(err, neith.ErrCacheExists) {
        return neith.FnErr(ctx, err)
    }
    return counter(ctx)
}

func counter(ctx context.Context) neith.FnComponent {
    count, err := neith.UseCache[int](ctx, "count")
    if err != nil {
        return neith.FnErr(ctx, err)
    }
    if err := count.Set(count.Value() + 1); err != nil {
        return neith.FnErr(ctx, err)
    }
    return neith.View(ctx, neith.HTML(fmt.Sprintf(`<p>%d</p>`, count.Value())))
}
```

Important cache errors are:

- `ErrCtxMissingDispatch`: operation was attempted outside a Neith context;
- `ErrCacheExists`: the key already exists for this client, even with another type;
- `ErrCacheNotFound`: no value exists for the key;
- `ErrCacheWrongType`: the key exists but was created as a different Go type.

### Timeout behavior

`Cache.Set(value, timeout...)` starts/refreshed expiry for the written value.

- no timeout argument -> `Config.CacheTimeOut`;
- `0` -> preserve an existing timeout when present;
- positive value shorter than `Config.CacheTimeOut` -> use that value;
- negative or too-large value -> fall back to `Config.CacheTimeOut`.

A stale watcher cannot delete a newer `Set` because expiry checks the update timestamp.

### History and callbacks

```go
cache.Record(true)
neith.OnCacheChange(cache, func() { log.Println("changed") })
neith.OnCacheTimeOut(cache, func() { log.Println("expired") })
_ = cache.Set(next)

history, ok := cache.History()
```

`Record(true)` affects future value updates; metadata-only changes do not trigger `OnCacheChange`.

## Immediate browser effects

Handlers can send small effects without rendering a region. Available convenience helpers include class operations and focused DOM changes:

```go
neith.AddClasses(ctx, "status", "active")
neith.RemoveClasses(ctx, "status", "pending")
neith.SetAttribute(ctx, "email", "aria-invalid", "true")
neith.RemoveAttribute(ctx, "email", "aria-invalid")
neith.SetStyle(ctx, "panel", "display", "none")
neith.RemoveStyle(ctx, "panel", "display")
neith.SetText(ctx, "status", "Saved")
neith.SetValue(ctx, "search", "")
neith.Focus(ctx, "search")
neith.Blur(ctx, "search")
neith.RemoveElement(ctx, "modal")
neith.RemoveTag(ctx, "dialog")
```

Use a normal `View` render for structural UI changes. Use focused DOM helpers for small, intentionally imperative mutations.

## Redirects and errors

Return a redirect from a handler with:

```go
return neith.RedirectURL(ctx, "/login")
```

Return an error through Neith's normal error path with:

```go
return neith.FnErr(ctx, err)
```

The underlying forms are `NewFn(ctx, nil).WithRedirect(url)` and `WithError(err)`.

## Calling browser JavaScript

Neith can call a named global function:

```go
return neith.NewFn(ctx, nil).JS("showToast", "Saved")
```

or dispatch it immediately:

```go
neith.JS(ctx, "showToast", "Saved")
```

The browser executes a function on `window` and sends its result back as a custom dispatch. Only use application-controlled function names and payloads.

## `ui` package

The optional `ui` package provides small renderer-agnostic components. It does not replace `templ`; mix them freely because both implement `neith.Component`.

```go
import "github.com/seanbman/neith/ui"

func form(ctx context.Context) neith.FnComponent {
    return neith.View(ctx,
        ui.Panel(
            ui.Heading("Profile", ui.Level(2)),
            ui.Form(
                ui.TextInput("name",
                    ui.Label("Name"),
                    ui.Required(true),
                ),
                ui.Select("status",
                    ui.Label("Status"),
                    ui.Options("active", "paused"),
                ),
                ui.Button("Save", ui.Type("submit"), ui.Primary()),
            ),
        ),
        neith.OnSubmit(save),
    )
}
```

Useful primitives include `Element`, `Fragment`, `Text`, `Panel`, `Stack`, `Row`, `Grid`, `Heading`, `Form`, `Button`, `HiddenInput`, `TextInput`, `TextArea`, `Select`, `Table`, and `Alert`, plus options for attributes, classes, labels, choices, table rows/columns, required/disabled state, and primary/secondary/danger presentation.

## Configuration

Package defaults currently include:

```text
CacheTimeOut     30 minutes
LogLevel         Error
UploadDir        os.TempDir()/neith-uploads
UploadMaxBytes   64 MiB
UploadMaxMemory  32 MiB
```

Set package configuration before mounting applications when possible:

```go
neith.SetConfig(&neith.Config{
    CacheTimeOut: 10 * time.Minute,
    LogLevel:     neith.Warn,
})
```

`Config.Set` creates a default logger when none is supplied and disables logging when `Silent` is true or `LogLevel` is `None`.

## Multiple Neith routes

Each call to `App` / `MiddleWareFn` owns a separate runtime:

```go
http.HandleFunc("/admin/", neith.App(adminApp,
    neith.ClientScript("/static/assets/neith.min.js"),
))
http.HandleFunc("/monitor/", neith.App(monitorApp,
    neith.ClientScript("/static/assets/neith.min.js"),
))
```

Even if the browser sends the same locally stored `neith_id` to both routes, caches and listeners are not shared across these runtime instances.

## Production checklist

Before exposing a Neith app publicly:

1. Put normal authentication and authorization in the host application; `neith_id` is a transport/session key, not identity proof.
2. Enforce origin policy at your reverse proxy or application boundary when cross-origin WebSocket access is not intended; the package's current WebSocket upgrader accepts all origins.
3. Serve over HTTPS so the browser selects `wss:`.
4. Decide whether embedded root assets or application-owned static assets fit your routing layout.
5. Set upload limits/directory deliberately and implement upload cleanup.
6. Choose `CacheTimeOut` with both reconnect tolerance and server memory retention in mind.
7. Avoid putting authorization decisions exclusively in browser DOM state; server handlers remain authoritative.
8. Run the Go and browser-client test suites described in [`DEVELOPMENT.md`](DEVELOPMENT.md).

## Error reference

Dispatch-related exported errors:

```text
ErrCtxMissingDispatch  context missing dispatch
ErrNoClientConnection  no connection to client
ErrConnectionNotFound  connection not found
ErrConnectionFailed    connection failed
ErrCtxMissingEvent     context missing event
```

Cache-related exported errors:

```text
ErrCacheNotFound       cache not found
ErrStoreNotFound       cache store not found; create cache first
ErrCacheWrongType      cache wrong type
ErrCacheExists         cache already exists; delete existing cache first
```

For function-by-function cache and component examples, continue with [`../notes/cache/README.md`](../notes/cache/README.md) and [`../notes/component/README.md`](../notes/component/README.md).