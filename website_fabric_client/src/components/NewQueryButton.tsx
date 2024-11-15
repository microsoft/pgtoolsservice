import { Button } from "@fluentui/react-components";
import { createNewQuery } from "@trident/relational-db-ux/lib/queries";
import { useDispatch, useSelector } from "react-redux";
import { StateStore } from "../state/store";
import { generateRequestId, normalizePath } from "../utils/helpers";

export const NewQueryButton = () => {
    const dispatch = useDispatch();
    const oeSessionId = useSelector(
        (state: StateStore) => state.db.objectExplorer.sessionId,
    );

    if (!oeSessionId) {
        return null;
    }

    return (
        <Button
            onClick={() => {
                dispatch(
                    createNewQuery({
                        parentPath: normalizePath(
                            `${oeSessionId}/Queries/MyQueries`,
                        ),
                        id: generateRequestId(),
                        initialContent: "SELECT * FROM example;",
                    }),
                );
            }}
        >
            New Query
        </Button>
    );
};
