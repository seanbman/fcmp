import WS from "jest-websocket-mock";
import { PROTOCOL_VERSION } from "../neith_types";

// Existing browser integration fixtures predate protocol versioning. Keep their
// payloads focused on the behavior under test while ensuring every mock server
// frame still crosses the same v1 wire boundary as production traffic.
const originalSend = WS.prototype.send;
WS.prototype.send = function (data: unknown) {
    const versioned = data !== null && typeof data === "object" && !("v" in data)
        ? { v: PROTOCOL_VERSION, ...(data as Record<string, unknown>) }
        : data;
    return originalSend.call(this, versioned as never);
};
