import { API } from "./api";
import { Dispatch } from "./neith_types";
import { emitHook } from "./hooks";

/**
 * Socket owns the browser's websocket connection to the Neith server.
 *
 * Session identity is intentionally not stored in JavaScript. The initial HTTP
 * page response establishes Neith's HttpOnly server-issued session cookie and
 * the browser includes that cookie automatically in the same-origin WebSocket
 * upgrade and reconnect requests.
 */
export class Socket {
    private ws: WebSocket | null = null;
    private addr: string | undefined = undefined;
    private api: API | null = null;
    private didConnect = false;
    private reconnectAttempts = 0;
    private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    private readonly baseReconnectDelay = 500;
    private readonly maxReconnectDelay = 30000;

    /** Tests may pass an explicit address; normal usage derives same-route WS(S). */
    constructor(addr?: string) {
        if (addr) {
            this.addr = addr;
        } else {
            this.init();
        }
        this.connect();
    }

    /** Builds the websocket address without embedding session identity in the URL. */
    private init() {
        const path = window.location.pathname || "/";
        const protocol = window.location.protocol === "https:" ? "wss" : "ws";
        this.addr = `${protocol}://${window.location.host}${path}`;
    }

    private connect() {
        try {
            this.ws = new WebSocket(this.addr);
        } catch (err) {
            throw new Error("ws: failed to connect to neith server: " + err);
        }
        try {
            this.api = new API(this.ws);
        } catch (err) {
            throw new Error("ws: failed to initiate API: " + err);
        }

        this.ws.onopen = () => {
            this.clearReconnectTimer();
            this.reconnectAttempts = 0;
            emitHook(this.didConnect ? "reconnect" : "connect");
            this.didConnect = true;
        };
        this.ws.onclose = (event) => {
            emitHook("disconnect");
            if (this.shouldReconnect(event)) {
                this.scheduleReconnect();
            }
        };
        this.ws.onerror = () => {};

        this.ws.onmessage = (event) => {
            const d = JSON.parse(event.data) as Dispatch;
            this.api?.Process(d);
        };
    }

    private shouldReconnect(event: CloseEvent): boolean {
        return typeof window !== "undefined" &&
            !event.wasClean &&
            event.code !== 1000 &&
            event.code !== 1001;
    }

    private scheduleReconnect() {
        if (this.reconnectTimer) return;

        const delay = Math.min(
            this.baseReconnectDelay * 2 ** this.reconnectAttempts,
            this.maxReconnectDelay
        );
        this.reconnectAttempts++;
        this.reconnectTimer = setTimeout(() => {
            this.reconnectTimer = null;
            this.connect();
        }, delay);
    }

    private clearReconnectTimer() {
        if (!this.reconnectTimer) return;
        clearTimeout(this.reconnectTimer);
        this.reconnectTimer = null;
    }
}
