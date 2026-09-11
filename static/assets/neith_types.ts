/** Current Neith server/browser wire protocol version. */
const PROTOCOL_VERSION = 1;

/**
 * Lookup table for browser-side dispatch handlers.
 *
 * The key is a protocol function name, and the value either performs a DOM
 * effect or returns a response dispatch that should be sent back to Go.
 */
type DispatchFunctions = {
    [key: string]: (data: Dispatch) => Dispatch | void;
};

/** Protocol function names shared by Go and the browser client. */
enum Fun {
    AUTH = "auth",
    KEY = "key",
    PING = "ping",
    RENDER = "render",
    CLASS = "class",
    DOM = "dom",
    CUSTOM = "custom",
    REDIRECT = "redirect",
    EVENT = "event",
    ERROR = "error",
}

type FnAuth = { key: string; token: string; };

type FnEventListener = {
    id: string;
    target_id: string;
    on: string;
    action: string;
    method: string;
    form_data: string;
    data: Object;
    uploads?: Upload[];
    submitter?: EventTargetData | null;
};

type EventTargetData = {
    id: string;
    name: string;
    classList: string[];
    tagName: string;
    innerHTML: string;
    outerHTML: string;
    value: string;
    checked: boolean;
    disabled: boolean;
    hidden: boolean;
    style: string;
    attributes: string[];
    dataset: string[];
    selectedOptions: string[];
};

type Upload = {
    id: string;
    field_name: string;
    file_name: string;
    content_type: string;
    size: number;
    path: string;
};

type FnPing = { server: boolean; client: boolean; };

type FnRender = {
    target_id: string;
    tag: string;
    inner: boolean;
    outer: boolean;
    append: boolean;
    prepend: boolean;
    remove: boolean;
    html: string;
    event_listeners: FnEventListener[];
};

type FnClass = { target_id: string; remove: boolean; names: string[]; };

type FnDOM = { target_id: string; operation: string; name: string; value: string; };

type FnCustom = { function: string; data: Object; result: Object; };
type FnRedirect = { url: string; };
type FnError = { message: string; };

/** Full websocket message exchanged between Go and the browser. */
type Dispatch = {
    v: number;
    function: Fun;
    id: string;
    key: string;
    conn_id: string;
    handler_id: string;
    action: string;
    label: string;
    event: FnEventListener;
    ping: FnPing;
    render: FnRender;
    class: FnClass;
    dom: FnDOM;
    redirect: FnRedirect;
    custom: FnCustom;
    error: FnError;
};

export {
    PROTOCOL_VERSION,
    DispatchFunctions,
    Fun,
    FnAuth,
    FnPing,
    FnRender,
    FnClass,
    FnDOM,
    FnCustom,
    FnRedirect,
    FnError,
    FnEventListener,
    EventTargetData,
    Upload,
    Dispatch,
};
