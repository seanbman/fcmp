package neith

import "encoding/json"

// ProtocolVersion is the current Neith server/browser wire protocol version.
// Incompatible protocol changes must increment this value and update the
// browser runtime plus contract tests in the same change.
const ProtocolVersion = 1

// functionName selects the browser/client operation represented by a dispatch.
type functionName string

const (
	ping     functionName = "ping"
	render   functionName = "render"
	class    functionName = "class"
	dom      functionName = "dom"
	redirect functionName = "redirect"
	event    functionName = "event"
	custom   functionName = "custom"
	fnError  functionName = "error"
)

func newDispatch(key string) *Dispatch {
	return &Dispatch{
		Version: ProtocolVersion,
		Key:     key,
		rt:      defaultRuntime,
	}
}

// Dispatch is the websocket message exchanged by Go and the browser client.
//
// Version identifies the wire contract. The current flat payload remains a
// compatibility shape while Phase 2 moves toward a stricter versioned message
// envelope. Function selects which nested payload is active for a message.
type Dispatch struct {
	buf        []byte        `json:"-"`
	conn       *conn         `json:"-"`
	rt         *runtime      `json:"-"`
	Version    int           `json:"v"`
	ID         string        `json:"id"`
	Key        string        `json:"key"`
	ConnID     string        `json:"conn_id"`
	HandlerID  string        `json:"handler_id"`
	Action     string        `json:"action"`
	Label      string        `json:"label"`
	Function   functionName  `json:"function"`
	FnEvent    EventListener `json:"event"`
	FnPing     FnPing        `json:"ping"`
	FnRender   FnRender      `json:"render"`
	FnClass    FnClass       `json:"class"`
	FnDOM      FnDOM         `json:"dom"`
	FnRedirect FnRedirect    `json:"redirect"`
	FnCustom   FnCustom      `json:"custom"`
	FnError    FnError       `json:"error"`
}

func (d Dispatch) validVersion() bool {
	return d.Version == ProtocolVersion
}

func (d Dispatch) validInboundFunction() bool {
	switch d.Function {
	case ping, event, custom, fnError:
		return true
	default:
		return false
	}
}

// listenerStrings serializes listener metadata for the rendered wrapper's
// events attribute.
func (f *FnRender) listenerStrings() string {
	b, err := json.Marshal(f.EventListeners)
	if err != nil {
		return ""
	}
	return string(b)
}
