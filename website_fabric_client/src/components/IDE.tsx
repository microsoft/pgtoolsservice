import { Stack } from "@fluentui/react";
import PgObjectExplorer from "./PgObjectExplorer";
import { QueryEditorComponent } from "./QueryEditorComponent";
import { NewQueryButton } from "./NewQueryButton";
import DbConnectForm from "./DbConnectForm";
import { useSocket } from "../hooks/sockets";
import { makeStyles } from "@fluentui/react-components";
import { useSelector } from "react-redux";
import { selectIsDbConnected, StateStore } from "../state/store";

export const IDE = () => {
    const styles = useStyles();

    // Initialize the websocket connections that will provide responses and
    // notifications from PGTS API requests
    useSocket();

    // Don't show the OE until there is a specific connection available
    const oeSessionId = useSelector(
        (state: StateStore) => state.db.objectExplorer.sessionId,
    );

    // New queries can't be run until there is a database connection
    const isDbConnected = useSelector(selectIsDbConnected);

    return (
        <>
            <DbConnectForm />
            {isDbConnected && <NewQueryButton />}
            <Stack horizontal horizontalAlign="space-between">
                {oeSessionId && (
                    <>
                        <div className={styles.objectExplorer}>
                            <PgObjectExplorer artifactId={oeSessionId} />
                        </div>
                        <div className={styles.editor}>
                            <QueryEditorComponent />
                        </div>
                    </>
                )}
            </Stack>
        </>
    );
};

const useStyles = makeStyles({
    editor: {
        height: "60vh",
        width: "600px",
        border: "1px solid black",
    },
    objectExplorer: {
        height: "60vh",
        width: "400px",
        border: "1px solid black",
    },
});
