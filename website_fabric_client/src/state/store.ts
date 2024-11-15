import { configureStore, EntityId } from "@reduxjs/toolkit";
import { combineEpics, createEpicMiddleware } from "redux-observable";
import {
    findNodeByPathInState,
    getSharedSlice /** reducers that manage caching nodes in the store */,
    getLoadNodesEpics /** epics that manage triggering async calls to load the nodes */,
    RootState,
} from "@trident/relational-db-ux/lib/sharedStore";
import { EpicMiddleWareDependencies } from "@trident/relational-db-ux/lib/types/epic.types";
import { loadNodesEpicRequests } from "./loadNodesEpicRequests"; /** We will define and import loadNodesEpicRequests in another file */
import {
    getQueryExecutionEpics,
    queryExtraReducersForSharedState,
} from "@trident/relational-db-ux/lib/queries";
import { editorExtraReducersForSharedState } from "@trident/relational-db-ux/lib/monaco-editor";
import { queryExecutionEpicRequests } from "./queryExecutionEpicRequests";
import { dbSlice, DBState } from "./dbSlice";

export type StateStore = RootState & { db: DBState };
const epicDependencies: EpicMiddleWareDependencies = {
    dispatch: (action) => store.dispatch(action),
};
const epicMiddleware = createEpicMiddleware({ dependencies: epicDependencies });

const store = configureStore({
    reducer: {
        // The slice provided by the Fabric UX controls
        shared: getSharedSlice([
            editorExtraReducersForSharedState,
            queryExtraReducersForSharedState,
        ]).reducer,

        // State for managing interactions with the PGTS
        db: dbSlice.reducer,
    },
    middleware: (getDefaultMiddleware) =>
        getDefaultMiddleware().concat(epicMiddleware),
});

epicMiddleware.run(
    combineEpics(
        // Epics that manage loading nodes in the OE
        getLoadNodesEpics(loadNodesEpicRequests),

        // Epics that manage executing queries
        getQueryExecutionEpics(queryExecutionEpicRequests),
    ),
);

export const selectIsDbConnected = (state: StateStore) => {
    return !!state.db.connection.info?.connectionId;
};

export const selectIsDbConnecting = (state: StateStore) => {
    return !!(state.db.connection.options && !state.db.connection.info);
};

export const getObjectExplorerFlatNodeByPath = (
    state: StateStore,
    id: EntityId,
) => findNodeByPathInState(state.shared, id);

export default store;
