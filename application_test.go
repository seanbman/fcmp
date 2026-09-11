package neith

import (
	"context"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

func TestApplicationServesRegisteredRoute(t *testing.T) {
	app := New()
	app.Route("/", func(context.Context) FnComponent { return FnComponent{} }, Title("Home"))

	req := httptest.NewRequest(http.MethodGet, "/", nil)
	res := httptest.NewRecorder()
	app.ServeHTTP(res, req)

	if res.Code != http.StatusOK {
		t.Fatalf("expected status 200, got %d", res.Code)
	}
	if !strings.Contains(res.Body.String(), "<title>Home</title>") {
		t.Fatalf("expected route page title, body=%q", res.Body.String())
	}
}

func TestApplicationRoutesShareRuntime(t *testing.T) {
	app := New()
	noop := func(context.Context) FnComponent { return FnComponent{} }
	app.Route("/", noop)
	app.Route("/settings", noop)

	if got := len(app.rt.handlers.pool); got != 2 {
		t.Fatalf("expected two route handlers in one runtime, got %d", got)
	}
}

func TestApplicationsAreRuntimeIsolated(t *testing.T) {
	appA := New()
	appB := New()

	if appA.rt == appB.rt {
		t.Fatal("separate applications must not share a runtime")
	}
	if &appA.rt.sessions == &appB.rt.sessions {
		t.Fatal("separate applications must not share session registries")
	}
}

func TestApplicationConfigDoesNotMutateLegacyGlobal(t *testing.T) {
	legacyTimeout := config.CacheTimeOut
	custom := *defaultConfig()
	custom.CacheTimeOut = 7 * time.Minute

	app := New(WithConfig(custom))

	if app.rt.Config().CacheTimeOut != 7*time.Minute {
		t.Fatalf("expected application timeout 7m, got %s", app.rt.Config().CacheTimeOut)
	}
	if config.CacheTimeOut != legacyTimeout {
		t.Fatalf("application construction mutated legacy global config: before=%s after=%s", legacyTimeout, config.CacheTimeOut)
	}
}

func TestInteractiveAuthorizationRejectsUploadBeforeSessionHandling(t *testing.T) {
	app := New(WithInteractiveAuthorization(func(*http.Request) bool { return false }))
	app.Route("/", func(context.Context) FnComponent { return FnComponent{} })

	req := httptest.NewRequest(http.MethodPost, "/?neith_upload=1", nil)
	res := httptest.NewRecorder()
	app.ServeHTTP(res, req)

	if res.Code != http.StatusForbidden {
		t.Fatalf("expected forbidden upload, got %d", res.Code)
	}
}

func TestInteractiveAuthorizationRejectsWebSocketBeforeUpgrade(t *testing.T) {
	app := New(WithInteractiveAuthorization(func(*http.Request) bool { return false }))
	app.Route("/", func(context.Context) FnComponent { return FnComponent{} })

	req := httptest.NewRequest(http.MethodGet, "/", nil)
	req.Header.Set("Connection", "Upgrade")
	req.Header.Set("Upgrade", "websocket")
	req.Header.Set("Sec-WebSocket-Version", "13")
	res := httptest.NewRecorder()
	app.ServeHTTP(res, req)

	if res.Code != http.StatusForbidden {
		t.Fatalf("expected forbidden websocket upgrade, got %d", res.Code)
	}
}

func TestApplicationShutdownClosesRuntimeAndRejectsRequests(t *testing.T) {
	app := New()
	app.Route("/", func(context.Context) FnComponent { return FnComponent{} })

	if err := app.Shutdown(context.Background()); err != nil {
		t.Fatalf("shutdown application: %v", err)
	}
	select {
	case <-app.Done():
	default:
		t.Fatal("application Done channel should close when shutdown begins")
	}

	req := httptest.NewRequest(http.MethodGet, "/", nil)
	res := httptest.NewRecorder()
	app.ServeHTTP(res, req)
	if res.Code != http.StatusServiceUnavailable {
		t.Fatalf("expected status 503 after shutdown, got %d", res.Code)
	}
}

func TestApplicationShutdownIsIdempotent(t *testing.T) {
	app := New()
	if err := app.Shutdown(context.Background()); err != nil {
		t.Fatalf("first shutdown: %v", err)
	}
	if err := app.Shutdown(context.Background()); err != nil {
		t.Fatalf("second shutdown: %v", err)
	}
	if err := app.Close(); err != nil {
		t.Fatalf("close after shutdown: %v", err)
	}
}

func TestRuntimeShutdownClosesTrackedConnection(t *testing.T) {
	app := New()
	if !app.rt.trackConnection() {
		t.Fatal("expected runtime to accept connection before shutdown")
	}
	c := &conn{
		rt:       app.rt,
		done:     make(chan struct{}),
		tracked:  true,
		ClientID: "client",
		Messages: make(chan []byte, 1),
	}
	app.rt.sessions.Attach(c.ClientID, c)

	if err := app.Shutdown(context.Background()); err != nil {
		t.Fatalf("shutdown application: %v", err)
	}
	select {
	case <-c.done:
	default:
		t.Fatal("tracked connection should be closed by application shutdown")
	}
	if _, ok := app.rt.sessions.ActiveConn(c.ClientID); ok {
		t.Fatal("shutdown should detach the active connection")
	}
}
