import { LoadChildNodesResponse } from "@trident/relational-db-ux/lib/sharedStore";
import { Deferred } from "../types";
import { SqlResultsEntity } from "@trident/relational-db-ux/lib/queries";

// Returns a random string that can be used as a request ID to the HTTP "RPC" server
export function generateRequestId(): string {
    return Math.random().toString(36);
}

// Drops a trailing slash, see normalizePath
export function trimUri(uri: string): string {
    return uri.replace(/\/$/, "");
}

// The Fabric Object Explorer uses an artifact ID that is the same as the
// session ID returned by PGTS, however, trailing slashes are required for
// string equality in PGTS key lookups, but cause double `//` in the nodePath of
// the Tree items in the OE. As part of this demonstration, that discrepency
// wasn't address but simply worked around by wrapping everything in this
// cleaner function.
export function normalizePath(s: string): string {
    const prefix = "objectexplorer://";
    if (s.startsWith(prefix)) {
        const rest = s.substring(prefix.length);
        const restNormalized = rest.replace(/\/+/g, "/");
        return prefix + restNormalized;
    } else {
        return s;
    }
}

// A utility for creating a Deferred object, which is a Promise that can be
// resolved or rejected from outside the Promise itself, via the returned method.
export function createDeferred<T>(): Deferred<T> {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let reject: (reason?: any) => void = () => {};
    let resolve: (value: T | PromiseLike<T>) => void = () => {};
    const promise = new Promise<T>((res, rej) => {
        resolve = res;
        reject = rej;
    });
    return { promise, resolve, reject };
}

// When a request to objectexplorer/expand is made, a corresponding Promise is
// set here, keyed by the `nodePath` which is being expanded. The promise is
// returned to the components that expect a LoadChildNodesResponse value in
// response. When subsequent messages are received over the socket, the
// `nodePath` is used to map that response back to this promise, and resolve it
// with the appropriate values.
export const pendingExpandResponses: Map<
    string,
    Deferred<LoadChildNodesResponse>
> = new Map();

// When a request to query/simpleexecute is made, a corresponding Promise is set
// here, keyed by the request ID. The promise is returned to the components
// that expect a SqlResultsEntity value in response.  When subsequent messages
// are received over the socket, the request ID is used to map that response
// back to this promise, and resolve it.
export const pendingExecuteResponses: Map<
    string,
    Deferred<SqlResultsEntity>
> = new Map();
