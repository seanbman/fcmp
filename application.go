package neith

import (
	"net/http"
	"sync"
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
func WithLogger(logger Logger) ApplicationOption {
	return func(c *Config) {
		c.Logger = logger.logger()
	}
}

// Logger is a small adapter that lets Neith accept its current logger without
// making Application depend on package-global configuration. Use Log with a
// charmbracelet/log logger. This adapter is temporary until the logging API is
// finalized before 1.0.
type Logger interface {
	logger() loggerValue
}

// loggerValue is intentionally private; the public logging surface will be
// finalized separately from runtime ownership.
type loggerValue interface{}

// New creates an isolated Neith Application.
func New(opts ...ApplicationOption) *Application {
	cfg := *defaultConfig()
	for _, opt := range opts {
		if opt != nil {
			opt(&cfg)
		}
	}
	cfg.SetLocal()

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

	page := NewPage(opts...)
	mounted := middleWareFnWithRuntime(a.rt, page.ServeHTTP, hf)

	a.mu.Lock()
	defer a.mu.Unlock()
	a.mux.HandleFunc(pattern, mounted)
}

// ServeHTTP serves embedded Neith assets and registered application routes.
func (a *Application) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	if a == nil || a.mux == nil {
		http.Error(w, "neith: application is not initialized", http.StatusInternalServerError)
		return
	}
	if serveEmbeddedAsset(w, r) {
		return
	}
	a.mux.ServeHTTP(w, r)
}
