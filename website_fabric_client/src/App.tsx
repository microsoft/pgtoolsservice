import "./App.css";
import { Provider } from "react-redux";
import { FluentProvider, webLightTheme } from "@fluentui/react-components";
import { TelemetryProvider } from "@trident/relational-db-ux/lib/providers";
import {
    createCertifiedEventEpicRequests,
    createLogEventEpicRequest,
    createTimedCertifiedEventEpicRequests,
} from "./state/telemetry";
import store from "./state/store"; /** Import the store we created and provide it to the rest of the app */
import { IDE } from "./components/IDE";
import { QueryClient, QueryClientProvider } from "react-query";

function App() {
    const queryClient = new QueryClient();

    return (
        <>
            <FluentProvider theme={webLightTheme}>
                <TelemetryProvider
                    certifiedEvent={createCertifiedEventEpicRequests()}
                    logEvent={createLogEventEpicRequest()}
                    timedCertifiedEvent={createTimedCertifiedEventEpicRequests()}
                >
                    <QueryClientProvider client={queryClient}>
                        <Provider store={store}>
                            <IDE />
                        </Provider>
                    </QueryClientProvider>
                </TelemetryProvider>
            </FluentProvider>
        </>
    );
}

export default App;
