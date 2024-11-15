import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import {
    ConnectionInfo,
    ConnectionOptions,
    ObjectExplorerSessionResponse,
} from "../types";

export type DBState = {
    connection: {
        options?: ConnectionOptions;
        info?: ConnectionInfo;
    };
    objectExplorer: {
        sessionId?: string;
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        rootNode?: any;
    };
    toolsService: {
        sessionId?: string;
    };
};

export const dbSlice = createSlice({
    name: "db",
    initialState: {
        connection: {
            options: undefined,
            info: undefined,
        },
        objectExplorer: {
            sessionId: undefined,
            rootNode: undefined,
        },
        toolsService: {
            sessionId: undefined,
        },
    } as DBState,
    reducers: {
        setSessionId(state, action: PayloadAction<string>) {
            state.toolsService.sessionId = action.payload;
        },
        setConnectionOptions(state, action: PayloadAction<ConnectionOptions>) {
            state.connection.options = action.payload;
        },
        setConnectionInfo(state, action: PayloadAction<ConnectionInfo>) {
            state.connection.info = action.payload;
        },
        clearConnection(state) {
            state.connection = {
                options: undefined,
                info: undefined,
            };
        },
        setObjectExplorerSessionCreated(
            state,
            action: PayloadAction<ObjectExplorerSessionResponse>,
        ) {
            state.objectExplorer = action.payload;
        },
    },
});

export const {
    setSessionId,
    setConnectionOptions,
    setConnectionInfo,
    clearConnection,
    setObjectExplorerSessionCreated,
} = dbSlice.actions;
