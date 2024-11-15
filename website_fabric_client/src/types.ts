export type ConnectionInfo = {
    connectionId: string;
    connectionSummary: {
        databaseName: string;
        serverName: string;
        userName: string;
    };
    serverInfo: {
        serverVersion: string;
        server: string;
        isCloud: boolean;
    };
    errorMessage?: string;
    ownerUri: string;
    type: string;
};

export type ConnectionParams = {
    owner_uri: string;
    connection: {
        options: {
            host: string;
            user: string;
            password: string;
            dbname: string;
        };
    };
};

export type ConnectionOptions = ConnectionParams["connection"]["options"];

export type ObjectExplorerSessionParams = {
    options: ConnectionOptions;
};

export type ObjectExplorerExpandParams = {
    sessionId: string;
    nodePath: string;
};

export type ObjectExplorerSessionResponse = {
    sessionId: string;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    rootNode: any;
};

export type SimpleExecuteParams = {
    owner_uri: string;
    queryString: string;
};

/*
Deferred<T> is a utility type that represents a promise that can be resolved or rejected by callers
after the promise has been created. This is useful for creating promises that are resolved or rejected
by external events, such as a user action or a network request.
*/
export interface Deferred<T> {
    promise: Promise<T>;
    resolve: (value: T | PromiseLike<T>) => void;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    reject: (reason?: any) => void;
}
