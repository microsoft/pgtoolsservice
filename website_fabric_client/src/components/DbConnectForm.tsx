import { useState } from "react";
import { useDbConnect, useCreateObjectExplorerSession } from "../hooks/api";
import { Input, Button, Spinner, MessageBar } from "@fluentui/react-components";
import { useDispatch, useSelector } from "react-redux";
import { selectIsDbConnecting, StateStore } from "../state/store";
import { ConnectionOptions, ConnectionParams } from "../types";
import { clearConnection, setConnectionOptions } from "../state/dbSlice";

const DbConnectForm = () => {
    const dispatch = useDispatch();
    const isConnecting = useSelector(selectIsDbConnecting);
    const connectionError = useSelector(
        (state: StateStore) => state.db.connection.info?.errorMessage,
    );
    const { mutate: connect } = useDbConnect();
    const { mutate: createOeSession } = useCreateObjectExplorerSession();

    const [formData, setFormData] = useState<ConnectionOptions>({
        host: "",
        user: "",
        password: "",
        dbname: "",
    });

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setFormData({
            ...formData,
            [name]: value,
        });
    };

    const handleConnect = () => {
        const connectionParams: ConnectionParams = {
            owner_uri: "hardcoded-owner-uri",
            connection: {
                options: formData,
            },
        };
        // Reset
        dispatch(clearConnection());
        dispatch(setConnectionOptions(formData));

        // Establish a query editor connection and persist the id (owner_uri) to the store
        connect(connectionParams);

        // Establish a separate connection for the object explorer session (session_id)
        createOeSession({
            options: formData,
        });
    };

    return (
        <div style={{ marginBottom: 10 }}>
            <form>
                <Input
                    type="text"
                    name="host"
                    value={formData.host}
                    onChange={handleChange}
                    placeholder="Host"
                />
                <Input
                    type="text"
                    name="user"
                    value={formData.user}
                    onChange={handleChange}
                    placeholder="User"
                />
                <Input
                    type="password"
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    placeholder="Password"
                />
                <Input
                    type="text"
                    name="dbname"
                    value={formData.dbname}
                    onChange={handleChange}
                    placeholder="Database Name"
                />
                <Button type="button" onClick={handleConnect}>
                    Connect
                </Button>
                {isConnecting && <Spinner label="Connecting..." />}
                {connectionError && (
                    <MessageBar intent="error">{connectionError}</MessageBar>
                )}
            </form>
        </div>
    );
};

export default DbConnectForm;
