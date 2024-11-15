import { useMutation, useQuery } from "react-query";
import axios from "axios";
import { LoadChildNodesResponse } from "@trident/relational-db-ux/lib/sharedStore";
import { SqlResultsEntity } from "@trident/relational-db-ux/lib/queries";
import { BASE_HTTP_URL } from "../utils/constants";
import {
    ConnectionParams,
    Deferred,
    ObjectExplorerExpandParams,
    ObjectExplorerSessionParams,
    SimpleExecuteParams,
} from "../types";
import {
    generateRequestId,
    pendingExpandResponses,
    pendingExecuteResponses,
} from "../utils/helpers";

type RpcParams = {
    [key: string]: string | number | boolean | null | RpcParams | RpcParams[];
};

// HTTP requests to the RPC server use this data type
const makeRpcBody = (method: string, requestId: string, params: RpcParams) => {
    return {
        jsonrpc: "2.0",
        id: requestId,
        method,
        params,
    };
};

// Create a new connection in PGTS for use when executing queries
export const useDbConnect = () => {
    return useMutation({
        mutationFn: async (connectionParams: ConnectionParams) => {
            const id = generateRequestId();
            const method = "connection/connect";
            const responseId = `${method}::${id}`;
            const body = makeRpcBody(method, responseId, connectionParams);

            const response = await axios.post(
                `${BASE_HTTP_URL}/json-rpc`,
                body,
                {
                    withCredentials: true,
                },
            );
            return response.data;
        },
    });
};

// Create a session (connection) in PGTS for the Object Explorer to use to navigate nodes
export const useCreateObjectExplorerSession = () => {
    return useMutation(
        async (connectionParams: ObjectExplorerSessionParams) => {
            const id = generateRequestId();
            const method = "objectexplorer/createsession";
            const responseId = `${method}::${id}`;
            const body = makeRpcBody(method, responseId, connectionParams);

            const response = await axios.post(
                `${BASE_HTTP_URL}/json-rpc`,
                body,
                {
                    withCredentials: true,
                },
            );
            return response.data;
        },
    );
};

// Establish a session with PGTS, which registers the websocket connection
export const useStartPgtsSession = () => {
    return useQuery(
        "start-session",
        async () => {
            return (
                await axios.post<string>(
                    `${BASE_HTTP_URL}/start-session`,
                    null,
                    {
                        withCredentials: true,
                    },
                )
            ).data;
        },
        { refetchOnWindowFocus: false },
    );
};

// Expand a node in the Object Explorer tree, set up a deferred object which can
// be completed when subsequent messages are received over the websockter
export const expandNode = async (
    expandParams: ObjectExplorerExpandParams,
    deferred: Deferred<LoadChildNodesResponse>,
) => {
    const id = generateRequestId();
    const method = "objectexplorer/expand";
    const deferredId = `${method}::${id}`;
    const body = makeRpcBody(method, deferredId, expandParams);
    pendingExpandResponses.set(expandParams.nodePath, deferred);

    setTimeout(() => {
        if (pendingExpandResponses.has(deferredId)) {
            pendingExpandResponses.delete(deferredId);
            deferred.reject(new Error("Request timed out"));
        }
    }, 10000);

    const response = await axios.post(`${BASE_HTTP_URL}/json-rpc`, body, {
        withCredentials: true,
    });
    return response.data;
};

// Execute a simple sql query, using an existing connection. The deferred object
// is set up to be completed when the response is received over the websocket
export const executeSqlOnConnection = async (
    executeParams: SimpleExecuteParams,
    deferred: Deferred<SqlResultsEntity>,
) => {
    const id = generateRequestId();
    const method = "query/simpleexecute";
    const deferredId = `${method}::${id}`;
    const body = makeRpcBody(method, deferredId, executeParams);

    pendingExecuteResponses.set(deferredId, deferred);

    const response = await axios.post(`${BASE_HTTP_URL}/json-rpc`, body, {
        withCredentials: true,
    });
    return response.data;
};
