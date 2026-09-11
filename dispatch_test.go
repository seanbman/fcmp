package neith

import (
	"encoding/json"
	"strings"
	"testing"
)

func TestDispatchJSONShape(t *testing.T) {
	dispatch := Dispatch{
		Version:  ProtocolVersion,
		ID:       "dispatch-1",
		Key:      "key-1",
		ConnID:   "conn-1",
		Function: render,
		FnRender: FnRender{
			TargetID: "content",
			Inner:    true,
			HTML:     "<p>Hello</p>",
		},
	}

	b, err := json.Marshal(dispatch)
	if err != nil {
		t.Fatalf("json.Marshal returned error: %v", err)
	}
	body := string(b)
	for _, want := range []string{
		`"v":1`,
		`"type":"render"`,
		`"conn_id":"conn-1"`,
		`"payload":{`,
		`"target_id":"content"`,
		`"html":"\u003cp\u003eHello\u003c/p\u003e"`,
	} {
		if !strings.Contains(body, want) {
			t.Fatalf("expected dispatch JSON to contain %s, got %s", want, body)
		}
	}
	for _, forbidden := range []string{`"function"`, `"buf"`, `"conn"`} {
		if strings.Contains(body, forbidden) {
			t.Fatalf("dispatch JSON leaked legacy/internal field %s: %s", forbidden, body)
		}
	}
}

func TestDispatchJSONRejectsUnknownEnvelopeField(t *testing.T) {
	var dispatch Dispatch
	err := json.Unmarshal([]byte(`{"v":1,"type":"ping","payload":{"server":true,"client":false},"surprise":true}`), &dispatch)
	if err == nil || !strings.Contains(err.Error(), "unknown field") {
		t.Fatalf("expected unknown envelope field error, got %v", err)
	}
}

func TestDispatchJSONRejectsUnknownPayloadField(t *testing.T) {
	var dispatch Dispatch
	err := json.Unmarshal([]byte(`{"v":1,"type":"ping","payload":{"server":true,"client":false,"surprise":true}}`), &dispatch)
	if err == nil || !strings.Contains(err.Error(), "unknown field") {
		t.Fatalf("expected unknown payload field error, got %v", err)
	}
}

func TestDispatchJSONRejectsUnsupportedVersion(t *testing.T) {
	var dispatch Dispatch
	err := json.Unmarshal([]byte(`{"v":2,"type":"ping","payload":{"server":true,"client":false}}`), &dispatch)
	if err == nil || !strings.Contains(err.Error(), "unsupported protocol version") {
		t.Fatalf("expected unsupported version error, got %v", err)
	}
}

func TestNewDispatchUsesCurrentProtocolVersion(t *testing.T) {
	d := newDispatch("client")
	if d.Version != ProtocolVersion {
		t.Fatalf("expected protocol version %d, got %d", ProtocolVersion, d.Version)
	}
	if !d.validVersion() {
		t.Fatal("new dispatch should satisfy current protocol version")
	}
}

func TestInboundFunctionAllowlist(t *testing.T) {
	for _, fn := range []functionName{ping, event, custom, fnError} {
		if !(Dispatch{Version: ProtocolVersion, Function: fn}).validInboundFunction() {
			t.Fatalf("expected %q to be accepted inbound", fn)
		}
	}
	for _, fn := range []functionName{render, class, dom, redirect, "unknown"} {
		if (Dispatch{Version: ProtocolVersion, Function: fn}).validInboundFunction() {
			t.Fatalf("expected %q to be rejected inbound", fn)
		}
	}
}

func TestFnRenderListenerStrings(t *testing.T) {
	render := FnRender{
		EventListeners: []EventListener{{
			ID:       "listener-1",
			TargetID: "button-1",
			On:       EventClick,
		}},
	}

	listeners := render.listenerStrings()
	for _, want := range []string{
		`"id":"listener-1"`,
		`"target_id":"button-1"`,
		`"on":"click"`,
	} {
		if !strings.Contains(listeners, want) {
			t.Fatalf("expected listener JSON to contain %s, got %s", want, listeners)
		}
	}
}
