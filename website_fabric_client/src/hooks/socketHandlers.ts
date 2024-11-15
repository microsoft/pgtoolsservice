import {
    DataGridResult,
    DataGridSchemaItem,
} from "@trident/relational-db-ux/lib/data-grid";
import {
    normalizePath,
    pendingExecuteResponses,
    pendingExpandResponses,
    trimUri,
} from "../utils/helpers";
import { SqlResultsEntity } from "@trident/relational-db-ux/lib/queries";
import { ExecutionStatus } from "@trident/relational-db-ux/lib/types";
import { FolderIconName } from "@trident/relational-db-ux/lib/icons";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function handleSimpleExecuteReponse(id: string, result: any) {
    const deferred = pendingExecuteResponses.get(id);
    if (!deferred) {
        console.error("No deferred found for id", id);
        return;
    }

    const columns: DataGridSchemaItem[] = result.columnInfo.map((column) => ({
        columnName: column.columnName,
        ordinal: column.columnOrdinal,
        dataType: "String", // column.dataType,
    }));

    const rows = result.rows.map((row: any, index: number) => ({
        index,
        data: row.map((value: any) => value.displayValue),
    }));

    const grid: DataGridResult = {
        schema: columns,
        rows: rows,
    };

    const queryResults: SqlResultsEntity = {
        messages: [],
        results: [grid],
        status: ExecutionStatus.Success,
        handle: "mockHandle",
        queryExecutionDurationInMs: 200,
    };
    deferred.resolve(queryResults);
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function handleExpandNodeNotification(params: any) {
    const deferred = pendingExpandResponses.get(params.nodePath);
    if (!deferred) {
        console.error("No deferred found for nodePath", params.nodePath);
        return;
    }
    const uri = trimUri(params.sessionId);
    const parentPath = normalizePath(
        params.nodePath.replace(uri, `${uri}/Server`),
    );
    const nodePath = normalizePath(params.sessionId + "/Server");
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const result = params.nodes.map((node: any) => ({
        path: `${nodePath}/${node.nodePath}`,
        entityType: node.nodeType,
        fluentIconLeft: FolderIconName,
        parentPath: parentPath,
        displayValue: node.label,
        isLeaf: node.isLeaf,
    }));
    deferred?.resolve({ treeNodes: result });
}
