import {
    LoadChildNodesResponse,
    LoadNodesEpicRequests,
    TreeNode,
} from "@trident/relational-db-ux/lib/sharedStore";
import { createTelemetryEpicRequests } from "./telemetry";
import { expandNode } from "../hooks/api";
import { createDeferred, normalizePath } from "../utils/helpers";
import { PromiseOrObservable } from "@trident/relational-db-ux/lib/types";
import {
    DatabaseIconName,
    FolderIconName,
} from "@trident/relational-db-ux/lib/icons";
import { QueryEntityType } from "@trident/relational-db-ux/lib/queries";
import store from "./store";

export const loadNodesEpicRequests: LoadNodesEpicRequests = {
    loadArtifact: (artifactPath) => {
        // Since Playground will have a single server, we hardcode the Artifact
        // at a single "Server" element
        return Promise.resolve({
            rootNodePaths: [
                normalizePath(`${artifactPath}/Server`),
                normalizePath(`${artifactPath}/Queries`),
            ],
            metadata: undefined,
        });
    },

    loadRootNode: (artifactPath, rootPath, correlationId) => {
        return getRootNode(artifactPath, rootPath, correlationId);
    },

    loadChildNodes: async (artifactPath, parentPath) => {
        // Queries are ephemeral object types created during the user session
        if (parentPath === normalizePath(`${artifactPath}/Queries`)) {
            return getQueriesNodes(parentPath);
        }
        // Database nodes are the actual database objects, as received from PGTS
        return getDatabaseNodes(parentPath);
    },
    ...createTelemetryEpicRequests(),
};

function getQueriesNodes(parentPath: string): Promise<LoadChildNodesResponse> {
    return Promise.resolve({
        treeNodes: [
            {
                path: normalizePath(`${parentPath}/MyQueries`),
                fluentIconLeft: FolderIconName,
                parentPath: parentPath,
                entityType: QueryEntityType.MyQueries,
                displayValue: "My Queries",
                isLeaf: false,
            },
        ],
    });
}

async function getDatabaseNodes(
    parentPath: string,
): Promise<LoadChildNodesResponse> {
    const oeSessionId = store.getState().db.objectExplorer.sessionId;
    if (!oeSessionId) {
        throw new Error("Object Explorer session ID not set");
    }
    const deferred = createDeferred<LoadChildNodesResponse>();

    const nodePath = normalizePath(parentPath.replace("Server", ""));

    await expandNode(
        {
            sessionId: oeSessionId,
            nodePath,
        },
        deferred,
    );

    return deferred.promise;
}

function getRootNode(
    artifactPath: string,
    rootPath: string,
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    correlationId: string,
): PromiseOrObservable<TreeNode> {
    // Since Playground will have a single server, we hardcode the Artifact
    // at a single "Server" and "Queries" element
    if (rootPath === normalizePath(`${artifactPath}/Queries`)) {
        return Promise.resolve({
            fluentIconLeft: DatabaseIconName,
            displayValue: "Queries",
            isLeaf: false,
            path: normalizePath(`${artifactPath}/Queries`),
            entityType: QueryEntityType.Queries,
            autoExpand: true,
        });
    } else {
        return Promise.resolve({
            fluentIconLeft: DatabaseIconName,
            displayValue: "Server",
            isLeaf: false,
            path: normalizePath(`${artifactPath}/Server`),
            entityType: "Database",
        });
    }
}
