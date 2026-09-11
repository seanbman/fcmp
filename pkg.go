// Package neith brings enhanced functionality to the Component interface.
package neith

import (
	"math"
	"net/http"
	"os"
	"time"

	"github.com/charmbracelet/log"
)

var config *Config

var logOpts = log.Options{
	ReportCaller:    true,
	ReportTimestamp: true,
	TimeFormat:      time.Kitchen,
	Prefix:          "package neith:",
}

type LogLevel log.Level

const (
	Debug LogLevel = -4
	Info  LogLevel = 0
	Warn  LogLevel = 4
	Error LogLevel = 8
	Fatal LogLevel = 12
	None  LogLevel = math.MaxInt32
)

func init() {
	config = defaultConfig()
	defaultRuntime = newRuntime(config)
}

func defaultConfig() *Config {
	return &Config{
		CacheTimeOut:             time.Minute * 30,
		LogLevel:                 Error,
		Logger:                   log.NewWithOptions(os.Stderr, logOpts),
		UploadDir:                "",
		UploadMaxBytes:           64 << 20,
		UploadMaxMemory:          32 << 20,
		WebSocketMaxMessageBytes: 1 << 20,
		SessionCookieName:        "neith_session",
		SessionCookiePath:        "/",
	}
}

type Config struct {
	Silent          bool          // If true, no logs will be printed
	CacheTimeOut    time.Duration // Default cache/session retention timeout
	LogLevel        LogLevel
	Logger          *log.Logger
	UploadDir       string // Directory for multipart event uploads; defaults to os.TempDir()/neith-uploads
	UploadMaxBytes  int64  // Maximum request size for one upload request
	UploadMaxMemory int64  // Maximum multipart memory before files spill to disk

	// WebSocketMaxMessageBytes limits one inbound WebSocket message. Values <= 0
	// are normalized to the secure default.
	WebSocketMaxMessageBytes int64

	// CheckOrigin optionally overrides Gorilla WebSocket's same-origin default.
	// Nil is the secure default and leaves Gorilla's host/origin validation active.
	CheckOrigin func(*http.Request) bool

	// SessionCookieName and SessionCookiePath configure Neith's server-issued
	// opaque session cookie. The cookie is always HttpOnly and SameSite=Lax.
	SessionCookieName string
	SessionCookiePath string

	// SessionCookieSecure forces the Secure flag, which is useful behind a trusted
	// TLS-terminating reverse proxy. Direct HTTPS requests are marked Secure
	// automatically even when this field is false.
	SessionCookieSecure bool
}

// SetConfig updates the legacy package-global configuration. New applications
// should prefer New with ApplicationOption values so configuration stays owned
// by the Application instance.
func SetConfig(c *Config) {
	if c == nil {
		c = defaultConfig()
	}
	c.setLocal()
	config = c
	if defaultRuntime != nil {
		defaultRuntime.config = config
	}
}

// Set updates the legacy package-global configuration. It is retained for
// compatibility; Application construction does not call it.
func (c *Config) Set() {
	SetConfig(c)
}

// setLocal normalizes configuration without mutating package-global state.
func (c *Config) setLocal() {
	if c.Logger == nil {
		c.Logger = log.NewWithOptions(os.Stderr, logOpts)
	}
	if c.WebSocketMaxMessageBytes <= 0 {
		c.WebSocketMaxMessageBytes = 1 << 20
	}
	if c.SessionCookieName == "" {
		c.SessionCookieName = "neith_session"
	}
	if c.SessionCookiePath == "" {
		c.SessionCookiePath = "/"
	}

	if c.Silent || c.LogLevel == None {
		c.Logger.SetLevel(log.Level(None))
		return
	}
	c.Logger.Info(
		"neith config set",
		"cache_timeout", c.CacheTimeOut,
		"log_level", c.LogLevel,
		"websocket_max_message_bytes", c.WebSocketMaxMessageBytes,
	)
	c.Logger.SetLevel(log.Level(c.LogLevel))
}
