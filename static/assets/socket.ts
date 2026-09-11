import { API } from "./api";
import { decodeMessage } from "./protocol";
import { emitHook } from "./hooks";

/** Socket owns the browser's websocket connection to the Neith server. */
export class Socket {
    private ws: WebSocket | null = null;
    private addr: string | undefined = undefined;
    private api: API | null = null;
    private didConnect = false;
    private reconnectAttempts = 0;
    private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    private readonly baseReconnectDelay = 500;
    private readonly maxReconnectDelay = 30000;

    constructor(addr?: string) {
        if (addr) this.addr = addr;
        else this.init();
        this.connect();
    }

    private init() {
        const path = window.location.pathname || "/";
        const protocol = window.location.protocol === "https:" ? "wss" : "ws";
        this.addr = `${protocol}://${window.location.host}${path}`;
    }

    private connect() {
        try {
            this.ws = new WebSocket(this.addr);
            this.api = new API(this.ws);
        } catch (err) {
            throw new Error("ws: failed to connect to neith server: " + err);
        }

        this.ws.onopen = () => {
            this.clearReconnectTimer();
            this.reconnectAttempts = 0;
            emitHook(this.didConnect ? "reconnect" : "connect");
            this.didConnect = true;
        };
        this.ws.onclose = (event) => {
            emitHook("disconnect");
            if (this.shouldReconnect(event)) this.scheduleReconnect();
        };
        this.ws.onerror = () => {};
        this.ws.onmessage = (event) => {
            try {
                this.api?.Process(decodeMessage(JSON.parse(event.data)));
            } catch (err) {
                emitHook("error", { error: err instanceof Error ? err.message : String(err) });
            }
        };
    }

    private shouldReconnect(event: CloseEvent): boolean {
        return typeof window !== "undefined" && !event.wasClean && event.code !== 1000 && event.code !== 1001;
    }

    private scheduleReconnect() {
        if (this.reconnectTimer) return;
        const delay = Math.min(this.baseReconnectDelay * 2 ** this.reconnectAttempts, this.maxReconnectDelay);
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
