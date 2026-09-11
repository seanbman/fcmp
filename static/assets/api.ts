import { addEventListeners, parseEventListeners } from "./events";
import type { Dispatch, DispatchFunctions } from "./neith_types";
import { Fun, PROTOCOL_VERSION } from "./neith_types";
import { emitHook } from "./hooks";
import { applyClass, applyCustom, applyDOM, applyRender } from "./render";

/**
 * API owns the browser side of the neith dispatch protocol.
 *
 * The websocket receives a Dispatch object from Go, validates the protocol
 * version, then routes that dispatch to a finite browser operation. Some
 * operations, such as ping and custom calls, produce a response dispatch sent
 * back over the same websocket.
 */
export class API {
    private ws: WebSocket | null = null;

    constructor(ws: WebSocket) {
        this.ws = ws;
    }

    public Process(d: Dispatch) {
        if (!d || d.v !== PROTOCOL_VERSION) {
            const version = d && typeof d.v === "number" ? d.v : "missing";
            emitHook("error", {
                dispatch: d,
                error: `unsupported protocol version: ${version}`,
            });
            return;
        }

        switch (d.function) {
            case Fun.REDIRECT:
                window.location.href = d.redirect.url;
                break;
            default:
                if (!this.funs[d.function]) {
                    this.Error(d, "function not found: " + d.function);
                    break;
                }
                const result = this.funs[d.function](d);
                if (!result) break;
                this.Dispatch(result);
                break;
        }
    }

    private Dispatch = (data: Dispatch | void) => {
        if (!data) return;
        if (!this.ws) {
            throw new Error("ws: not connected to server...");
        }
        if (data.v !== PROTOCOL_VERSION) {
            throw new Error(`unsupported protocol version: ${data.v}`);
        }
        this.ws.send(JSON.stringify(data));
    };

    private Error = (d: Dispatch, message: string) => {
        d.function = Fun.ERROR;
        d.error = { message };
        emitHook("error", { dispatch: d, error: message });
        this.Dispatch(d);
    };

    private funs: DispatchFunctions = {
        ping: (d: Dispatch) => {
            d.ping.client = true;
            return d;
        },
        render: (d: Dispatch) => {
            emitHook("beforeRender", { dispatch: d });
            const elem = applyRender(d, this.Error);
            if (!elem) return;

            const dispatch = parseEventListeners(elem, d);
            addEventListeners(dispatch, this.Dispatch, this.Error);
            emitHook("afterRender", { dispatch, element: elem });
            return;
        },
        class: (d: Dispatch) => applyClass(d, this.Error),
        dom: (d: Dispatch) => applyDOM(d, this.Error),
        custom: (d: Dispatch) => applyCustom(d, this.Error),
    };
}
