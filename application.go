package neith

import (
	"context"
	"net/http"
	"sync"

	"github.com/charmbracelet/log"
)

// Application is the canonical owner of a Neith runtime and its routes.
//
// Routes registered on one Application share the same runtime boundary.
// Separately created applications remain isolated. Application implements
// http.Handler and is intended to compose with ordinary Go HTTP middleware.
type Application struct {
	rt  *runtime
	mux *http.ServeMux
	mu  sync.Mutex
}

// ApplicationOption configures a new Application.
type ApplicationOption func(*Config)

// WithConfig applies a copy of c to a new Application. Later application
// options may override fields on that copy.
func WithConfig(c Config) ApplicationOption {
	return func(target *Config) {
		*target = c
	}
}

// WithLogger configures the application logger.
func WithLogger(logger *log.Logger) ApplicationOption {
	return func(c *Config) {
		c.Logger = logger
	}
}

// WithWebSocketMaxMessageBytes limits one inbound WebSocket message. A value
// <= 0 is normalized to Neith's secure default during application creation.
func WithWebSocketMaxMessageBytes(limit int64) ApplicationOption {
	return func(c *Config) {
		c.WebSocketMaxMessageBytes = limit
	}
}

// WithWebSocketOriginPolicy overrides the default same-origin WebSocket policy.
// Applications should only relax the default deliberately for trusted origins.
func WithWebSocketOriginPolicy(policy func(*http.Request) bool) ApplicationOption {
	return func(c *Config) {
		c.CheckOrigin = policy
	}
}

// New creates an isolated Neith Application.
func New(opts ...ApplicationOption) *Application {
	cfg := *defaultConfig()
	for _, opt := range opts {
		if opt != nil {
			opt(&cfg)
		}
	}
	cfg.setLocal()

	return &Application{
		rt:  newRuntime(&cfg),
		mux: http.NewServeMux(),
	}
}

// Route registers an interactive Neith route. Page options customize the
// document shell for this route. Route follows http.ServeMux pattern semantics.
func (a *Application) Route(pattern string, hf HandleFn, opts ...PageOption) {
	if a == nil {
		panic("neith: nil Application")
	}
	if hf == nil {
		panic("neith: nil route handler")
	}
	if a.rt == nil || a.rt.IsClosed() {
		panic("neith: cannot register route on closed Application")
	}

	page := NewPage(opts...)
	mounted := middleWareFnWithRuntime(a.rt, page.ServeHTTP, hf)

	a.mu.Lock()
	defer a.mu.Unlock()
	a.mux.HandleFunc(pattern, mounted)
}

// ServeHTTP serves embedded Neith assets and registered application routes.
func (a *Application) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	if a == nil || a.mux == nil || a.rt == nil {
		http.Error(w, "neith: application is not initialized", http.StatusInternalServerError)
		return
	}
	if a.rt.IsClosed() {
		http.Error(w, ErrApplicationClosed.Error(), http.StatusServiceUnavailable)
		return
	}
	if serveEmbeddedAsset(w, r) {
		return
	}
	a.mux.ServeHTTP(w, r)
}

// Done is closed when application shutdown begins.
func (a *Application) Done() <-chan struct{} {
	if a == nil || a.rt == nil {
		closed := make(chan struct{})
		close(closed)
		return closed
	}
	return a.rt.Done()
}

// Shutdown stops new application work, cancels the runtime context, closes
// active WebSocket connections, and waits for tracked connections to finish or
// for ctx to expire. Shutdown is safe to call more than once.
func (a *Application) Shutdown(ctx context.Context) error {
	if a == nil || a.rt == nil {
		return nil
	}
	if ctx == nil {
		ctx = context.Background()
	}
	return a.rt.Shutdown(ctx)
}

// Close shuts the application down without a deadline. It allows Application
// to participate in ordinary io.Closer-style lifecycle management.
func (a *Application) Close() error {
	return a.Shutdown(context.Background())
}
