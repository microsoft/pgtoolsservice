import {
    QueryExecutionEpicRequests,
    SqlResultsEntity,
} from "@trident/relational-db-ux/lib/queries";
import { createTelemetryEpicRequests } from "./telemetry";
import { MWCToken } from "@trident/extension-client";
import { executeSqlOnConnection } from "../hooks/api";
import { createDeferred } from "../utils/helpers";
import store from "./store";

async function getMWCToken() {
    return "";
}

async function executeSql(
    mwcToken: MWCToken,
    sql: string,
    querySessionId: string,
    correlationId: string,
): Promise<SqlResultsEntity> {
    console.log(`Executing SQL: ${sql}, ${querySessionId}, ${correlationId}`);
    const state = store.getState();
    const ownerUri = state.db.connection.info?.ownerUri;
    const deferred = createDeferred<SqlResultsEntity>();

    // Owner URI is the key with PGTS of an existing/active connection
    if (!ownerUri) {
        throw new Error("No ownerUri found");
    }

    await executeSqlOnConnection(
        {
            owner_uri: ownerUri,
            queryString: sql,
        },
        deferred,
    );

    return deferred.promise;
}

async function trackSql(
    mwcToken: MWCToken,
    batchId: string,
    _querySessionId: string,
    correlationId: string,
) {
    console.log(`Not implemented: Tracking SQL: ${batchId} ${_querySessionId}`);
}

async function cancelSql(
    mwcToken: MWCToken,
    _: string | undefined,
    queryId: string,
    correlationId: string,
): Promise<void> {
    console.warn("Not implemented: Canceling SQL", queryId);
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
async function openErrorDialog(error: any) {
    console.log("Not implemented: Opening error dialog", error);
}

export const queryExecutionEpicRequests: QueryExecutionEpicRequests = {
    getMWCToken,
    executeSql,
    trackSql,
    cancelSql,
    openErrorDialog,
    ...createTelemetryEpicRequests(),
};
