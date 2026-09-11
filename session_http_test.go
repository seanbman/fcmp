package neith

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestEnsureSessionIDIssuesOpaqueHttpOnlyCookie(t *testing.T) {
	rt := newRuntime(defaultConfig())
	req := httptest.NewRequest(http.MethodGet, "http://example.test/", nil)
	res := httptest.NewRecorder()

	id, err := rt.ensureSessionID(res, req)
	if err != nil {
		t.Fatalf("ensure session: %v", err)
	}
	if len(id) < 32 {
		t.Fatalf("expected opaque session id, got %q", id)
	}

	cookies := res.Result().Cookies()
	if len(cookies) != 1 {
		t.Fatalf("expected one session cookie, got %d", len(cookies))
	}
	cookie := cookies[0]
	if cookie.Name != "neith_session" || cookie.Value != id {
		t.Fatalf("unexpected session cookie: %#v", cookie)
	}
	if !cookie.HttpOnly {
		t.Fatal("session cookie must be HttpOnly")
	}
	if cookie.SameSite != http.SameSiteLaxMode {
		t.Fatalf("expected SameSite=Lax, got %v", cookie.SameSite)
	}
	if cookie.Path != "/" {
		t.Fatalf("expected cookie path /, got %q", cookie.Path)
	}
	if cookie.Secure {
		t.Fatal("plain HTTP development request should not force Secure without configuration")
	}
}

func TestEnsureSessionIDReusesExistingServerSession(t *testing.T) {
	rt := newRuntime(defaultConfig())
	req := httptest.NewRequest(http.MethodGet, "http://example.test/", nil)
	req.AddCookie(&http.Cookie{Name: "neith_session", Value: "existing-session"})
	res := httptest.NewRecorder()

	id, err := rt.ensureSessionID(res, req)
	if err != nil {
		t.Fatalf("ensure session: %v", err)
	}
	if id != "existing-session" {
		t.Fatalf("expected existing session, got %q", id)
	}
	if len(res.Result().Cookies()) != 0 {
		t.Fatal("existing session should not issue a replacement cookie")
	}
}

func TestEnsureSessionIDMarksDirectHTTPSAndConfiguredProxySecure(t *testing.T) {
	for _, tc := range []struct {
		name   string
		url    string
		forced bool
	}{
		{name: "direct https", url: "https://example.test/"},
		{name: "forced secure", url: "http://example.test/", forced: true},
	} {
		t.Run(tc.name, func(t *testing.T) {
			cfg := defaultConfig()
			cfg.SessionCookieSecure = tc.forced
			rt := newRuntime(cfg)
			req := httptest.NewRequest(http.MethodGet, tc.url, nil)
			res := httptest.NewRecorder()
			if _, err := rt.ensureSessionID(res, req); err != nil {
				t.Fatalf("ensure session: %v", err)
			}
			if cookies := res.Result().Cookies(); len(cookies) != 1 || !cookies[0].Secure {
				t.Fatalf("expected Secure session cookie, got %#v", cookies)
			}
		})
	}
}

func TestApplicationPageIssuesSessionCookie(t *testing.T) {
	app := New()
	app.Route("/", func(_ interfaceContext) FnComponent { return FnComponent{} })
}

type interfaceContext = interface{ Done() <-chan struct{} }
