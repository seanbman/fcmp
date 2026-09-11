package neith

import (
	"context"
	"sync"
)

type runtime struct {
	handlers       handlerPool
	sessions       clientSessionRegistry
	eventListeners eventListeners
	stores         storeManager
	cacheEvents    cacheEventRegistry
	config         *Config

	ctx       context.Context
	cancel    context.CancelFunc
	closeOnce sync.Once
	mu        sync.Mutex
	closed    bool
	connWG    sync.WaitGroup
}

var defaultRuntime *runtime

func newRuntime(config *Config) *runtime {
	if config == nil {
		config = defaultConfig()
	}
	ctx, cancel := context.WithCancel(context.Background())
	return &runtime{
		handlers:       newHandlerPool(),
		sessions:       newClientSessionRegistry(),
		eventListeners: newEventListeners(),
		stores:         newStoreManager(),
		cacheEvents:    newCacheEventRegistry(),
		config:         config,
		ctx:            ctx,
		cancel:         cancel,
	}
}

func (r *runtime) Config() *Config {
	if r == nil || r.config == nil {
		return config
	}
	return r.config
}

func (r *runtime) Context() context.Context {
	if r == nil || r.ctx == nil {
		return context.Background()
	}
	return r.ctx
}

func (r *runtime) Done() <-chan struct{} {
	return r.Context().Done()
}

func (r *runtime) IsClosed() bool {
	if r == nil {
		return true
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	return r.closed
}

func (r *runtime) trackConnection() bool {
	if r == nil {
		return false
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	if r.closed {
		return false
	}
	r.connWG.Add(1)
	return true
}

func (r *runtime) connectionClosed() {
	if r != nil {
		r.connWG.Done()
	}
}

func (r *runtime) Shutdown(ctx context.Context) error {
	if r == nil {
		return nil
	}

	r.closeOnce.Do(func() {
		r.mu.Lock()
		r.closed = true
		r.mu.Unlock()

		if r.cancel != nil {
			r.cancel()
		}
		for _, c := range r.sessions.ActiveConnections() {
			_ = c.close()
		}
	})

	finished := make(chan struct{})
	go func() {
		r.connWG.Wait()
		close(finished)
	}()

	select {
	case <-finished:
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}

func runtimeFromDispatch(details dispatchDetails) *runtime {
	if details.Runtime != nil {
		return details.Runtime
	}
	return defaultRuntime
}
