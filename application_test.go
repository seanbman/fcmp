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
