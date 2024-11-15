// hooks/useSocket.js
import { useEffect } from "react";
import io from "socket.io-client";
import { useDispatch } from "react-redux";
import { useStartPgtsSession } from "./api";
import {
    setConnectionInfo,
    setObjectExplorerSessionCreated,
    setSessionId,
} from "../state/dbSlice";
import { BASE_HTTP_URL } from "../utils/constants";
import {
    normalizePath,
    pendingExpandResponses,
    trimUri,
} from "../utils/helpers";
import { FolderIconName } from "@trident/relational-db-ux/lib/icons";
import {
    handleExpandNodeNotification,
    handleSimpleExecuteReponse,
} from "./socketHandlers";
// import { connectComplete, anotherEvent } from '../store/actions';

export const useSocket = () => {
    const dispatch = useDispatch();
    const { data: sessionId, error } = useStartPgtsSession();

    useEffect(() => {
        if (error) {
            console.error("Error starting session", error);
        }
    }, [error]);

    // Save the PGTS session ID when it is created
    useEffect(() => {
        if (sessionId) {
            dispatch(setSessionId(sessionId));
        }
    }, [dispatch, sessionId]);

    // Connect to the PGTS WebSocket server after the session is created on the server
    useEffect(() => {
        if (!sessionId) {
            return;
        }

        const socket = io(BASE_HTTP_URL, {
            transports: ["websocket"],
            reconnection: false,
        });

        socket.on("connect", () => {
            console.log("Socket.IO connection established");
        });

        socket.on("disconnect", () => {
            console.log("Socket.IO connection disconnected");
        });

        socket.on("connect_error", (error) => {
            console.error("Socket.IO connection error:", error);
        });

        // Handle incoming messages based on the 'method' attribute
        socket.on("notification", (data) => {
            const { method, params } = JSON.parse(data);
            console.log("recieved notification", method, params);

            switch (method) {
                case "connection/complete":
                    dispatch(setConnectionInfo(params));
                    break;
                case "objectexplorer/sessioncreated":
                    dispatch(setObjectExplorerSessionCreated(params));
                    break;
                case "objectexplorer/expandCompleted":
                    handleExpandNodeNotification(params);
                    break;
                default:
                    console.warn(`Unhandled method: ${method}`);
            }
        });

        socket.on("response", (data) => {
            const { id, result } = JSON.parse(data);
            const method = id.split("::")[0];
            console.log("Recieved response:", id, result);

            switch (method) {
                case "connection/connect":
                    // We can ignore this response, the notification of the same name will handle all cases
                    break;
                case "objectexplorer/createsession":
                    dispatch(setObjectExplorerSessionCreated(result));
                    break;
                case "objectexplorer/expand":
                    break;
                case "query/simpleexecute":
                    handleSimpleExecuteReponse(id, result);
                    break;
                default:
                    console.warn(`Unhandled response id: ${id}`);
            }
        });

        socket.on("error", (error) => {
            console.error("Socket.IO error:", error);
        });

        // Clean up on component unmount
        return () => {
            socket.disconnect();
        };
    }, [dispatch, sessionId]);
};
