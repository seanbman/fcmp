import WS from "jest-websocket-mock";
import { Socket } from "../socket";
import {
    describe,
    beforeAll,
    test,
    afterAll,
    expect,
    beforeEach,
} from "@jest/globals";
import { JSDOM } from "jsdom";
import { Dispatch, Fun } from "../fncmp_types";

describe("test websocket functions", () => {
    let dispatches: Dispatch[] = [];
    let server: WS;
    let socket: Socket;

    // Wait for a callback to return true
    async function waitCallback(callback: () => boolean) {
        return new Promise((resolve) => {
            const check = () => {
                setTimeout(() => {
                    if (callback()) {
                        resolve(null);
                    } else {
                        check();
                    }
                }, 25);
            };
            check();
        });
    }

    beforeAll(async () => {
        // Create a new websocket server
        server = new WS("ws://localhost:1234", { jsonProtocol: true });
        server.on("connection", (socket) => {
            // When the server receives a message, parse it and add it to the dispatches array
            socket.on("message", (message) => {
                console.log("server received message from API: ", message.toString());
                const msg: Dispatch = JSON.parse(message.toString());
                dispatches.push(msg);
            });
        });
        // Create a new Socket client
        socket = new Socket("ws://localhost:1234");
        await server.connected;
    });

    beforeEach(async () => {
        // Wait for api to process previous dispatches
        await new Promise((resolve) => setTimeout(resolve, 500));
        dispatches = [];
        const jsdom = new JSDOM(
            "<!DOCTYPE html><html><body><main><p>test</p></main></body></html>"
        );
        global.document = jsdom.window.document;
    });

    test("test ping", async () => {
        const dispatch = {
            function: Fun.PING,
            ping: {
                server: true,
                client: false,
            },
        };
        server.send(dispatch);
        await waitCallback(() => dispatches.length > 0);
        expect(dispatches.length).toEqual(1);
        expect(dispatches[0].ping.client).toEqual(true);
    });

    const test_cases = [
        {
            tag: "main",
            name: "test render inner",
            html: "<p>test render inner</p>",
            inner: true,
            expected: "<p>test render inner</p>",
        },
        {
            tag: "main",
            name: "test render append",
            html: "<p>test render append</p>",
            append: true,
            expected: "<p>test</p><p>test render append</p>",
        },
        {
            tag: "main",
            name: "test render prepend",
            html: "<p>test render prepend</p>",
            prepend: true,
            expected: "<p>test render prepend</p><p>test</p>",
        },
        {
            tag: "main",
            name: "test render outer",
            html: "<p>test</p>",
            outer: true,
            expected: "",
        },
        {
            tag: "main",
            name: "test render remove",
            html: "",
            remove: true,
            expected: "",
        },
    ];

    test_cases.forEach((test_case) => {
        test(test_case.name, async () => {
            const dispatch = {
                function: Fun.RENDER,
                render: {
                    tag: test_case.tag,
                    html: test_case.html,
                    inner: test_case.inner,
                    append: test_case.append,
                    prepend: test_case.prepend,
                    outer: test_case.outer,
                    remove: test_case.remove,
                },
            } as Dispatch;
            server.send(dispatch);

            let html: string = "";
            await waitCallback(() => {
                if (dispatch.render.tag !== "")
                    html =
                        document.querySelector(dispatch.render.tag)
                            ?.innerHTML ?? "";    
                else
                    html =
                        document.getElementById(dispatch.render.target_id)
                            ?.innerHTML ?? "";
                return html === test_case.expected;
            });
            expect(html).toEqual(test_case.expected);
        });
    });

    test("test event listener", async () => {
        // Setup on focus event listener for a button
        const event = {
            id: "_",
            target_id: "test",
            on: "focus",
            action: "test",
            method: "GET",
            form_data: "",
            data: {},
        };
        const dispatch = {
            function: Fun.RENDER,
            render: {
                tag: "main",
                html: `<div id="${event.target_id}" events=[${JSON.stringify(
                    event
                )}]><button id="test_button">Test</button></div>`,
                append: true,
            },
        };

        server.send(dispatch);
        await waitCallback(() => {
            const elem = document.querySelector("button");
            if(!elem) return false;
            elem.focus();
            return true;
        });
        await waitCallback(() => dispatches.length > 0);
        expect(dispatches[0].event.target_id).toEqual(event.target_id);
    });

    test("test error", async () => {
        const dispatch = {
            function: Fun.RENDER,
            render: {
                tag: "test",
                html: "<p>test</p>",
                inner: true,
            }
        };
        server.send(dispatch);
        await waitCallback(() => dispatches.length > 0);
        expect(dispatches[0].error.message).toBeDefined();
    });

    afterAll(() => {
        WS.clean();
    });
});
