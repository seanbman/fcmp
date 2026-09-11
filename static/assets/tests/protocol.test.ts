import { describe, expect, test } from "@jest/globals";
import { API } from "../api";
import { onHook } from "../hooks";
import { Dispatch, Fun, PROTOCOL_VERSION } from "../neith_types";

describe("protocol version boundary", () => {
    test("rejects unsupported versions without executing or replying", () => {
        const sent: string[] = [];
        const ws = { send: (message: string) => sent.push(message) } as unknown as WebSocket;
        const api = new API(ws);
        const errors: string[] = [];
        const off = onHook("error", (payload: any) => errors.push(String(payload.error)));

        api.Process({
            v: PROTOCOL_VERSION + 1,
            function: Fun.RENDER,
            render: { tag: "main", html: "<p>must not render</p>", inner: true },
        } as Dispatch);

        expect(sent).toHaveLength(0);
        expect(errors).toHaveLength(1);
        expect(errors[0]).toContain("unsupported protocol version");
        off();
    });

    test("rejects a missing version", () => {
        const sent: string[] = [];
        const ws = { send: (message: string) => sent.push(message) } as unknown as WebSocket;
        const api = new API(ws);
        const errors: string[] = [];
        const off = onHook("error", (payload: any) => errors.push(String(payload.error)));

        api.Process({
            function: Fun.PING,
            ping: { server: true, client: false },
        } as Dispatch);

        expect(sent).toHaveLength(0);
        expect(errors[0]).toContain("unsupported protocol version: missing");
        off();
    });

    test("v1 ping replies preserve the negotiated version", () => {
        const sent: string[] = [];
        const ws = { send: (message: string) => sent.push(message) } as unknown as WebSocket;
        const api = new API(ws);

        api.Process({
            v: PROTOCOL_VERSION,
            function: Fun.PING,
            ping: { server: true, client: false },
        } as Dispatch);

        expect(sent).toHaveLength(1);
        const response = JSON.parse(sent[0]) as Dispatch;
        expect(response.v).toBe(PROTOCOL_VERSION);
        expect(response.ping.client).toBe(true);
    });
});
