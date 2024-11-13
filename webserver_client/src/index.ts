import { io, Socket } from "socket.io-client";
import { EditorState } from "@codemirror/state";
import { EditorView, basicSetup } from "codemirror"; // Updated import
import { json } from "@codemirror/lang-json";

let jsonEditor: EditorView | null = null;

function initializeEditor() {
    // Dispose of the previous editor instance if needed
    if (jsonEditor) {
        jsonEditor.destroy();
        jsonEditor = null;
    }

    jsonEditor = new EditorView({
        state: EditorState.create({
            extensions: [basicSetup, json()] // Use basicSetup from "codemirror"
        }),
        parent: document.getElementById("jsonEditorContainer") as HTMLElement
    });
}

// Function to display messages in the output window
function logToOutput(message: string, isError = false): void {
    const outputMessages = document.getElementById("outputMessages");
    if (outputMessages) {
        const newMessage = document.createElement("li");
        newMessage.textContent = message;
        if (isError) {
            newMessage.style.color = "red"; // Make the message text red
        }
        outputMessages.appendChild(newMessage);
        outputMessages.scrollTop = outputMessages.scrollHeight; // Auto-scroll to the latest message
    }
}

// Function to start the session
async function startSession(): Promise<void> {
    logToOutput("Attempting to connect to the server...");
    try {
        const response = await fetch("http://localhost:5000/start-session", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({}), // Add any necessary data here
            credentials: "include", // Ensure cookies are included in the request
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        logToOutput("Session started: " + JSON.stringify(data));

        // Connect to the Socket.IO server after starting the session
        connectToSocket();
    } catch (error) {
        if (error instanceof Error) {
            logToOutput("Failed to start session: " + error.message, true);
        } else {
            logToOutput("Failed to start session: Unknown error", true);
        }
    }
}

// Function to connect to the Socket.IO server
function connectToSocket(): void {
    const socket: Socket = io("http://localhost:5000", {
        withCredentials: true, // Ensure cookies are sent with the WebSocket handshake
    });

    // Event listener for connection
    socket.on("connect", () => {
        logToOutput("Connected to server");
        // Show the chat interface after establishing the connection
        const chatInterface = document.getElementById("chatInterface");
        if (chatInterface) {
            initializeEditor();
            chatInterface.style.display = "block";
        }
    });

    // Event listener for disconnection
    socket.on("disconnect", () => {
        logToOutput("Disconnected from server");
        // Hide the chat interface after disconnection
        const chatInterface = document.getElementById("chatInterface");
        if (chatInterface) {
            chatInterface.style.display = "none";
        }
    });


    // Event listener for reconnecting
    socket.on("reconnect_attempt", () => {
        logToOutput("Attempting to reconnect to server...");
    });

    // Event listener for receiving response from the server
    socket.on("response", (data: string) => {
        logToOutput("Server (response): " + data);
    });

    // Event listener for receiving notification from the server
    socket.on("notification", (data: string) => {
        logToOutput("Server (notification): " + data);
    });

    // Event listener for receiving error messages from the server
    socket.on("error", (data: string) => {
        logToOutput("Server (error): " + data, true);
    });

    // Function to send message to the server via HTTP
    (window as any).sendMessage = async () => {
        if (!jsonEditor) {
            console.error("JSON editor not initialized.");
            return;
        }

        // Get the JSON input from CodeMirror
        const message = jsonEditor.state.doc.toString();
        if (message) {
            logToOutput("You: " + message);
            try {
                const response = await fetch("http://localhost:5000/json-rpc", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: message,
                    // body: JSON.stringify({
                    //     jsonrpc: "2.0",
                    //     method: "sendMessage",
                    //     params: { message },
                    //     id: 1,
                    // }),
                    credentials: "include",
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();

                // Clear the editor after sending
                jsonEditor.dispatch({
                    changes: { from: 0, to: jsonEditor.state.doc.length, insert: "" },
                });
            } catch (error) {
                if (error instanceof Error) {
                    logToOutput("Failed to send message: " + error.message, true);
                } else {
                    logToOutput("Failed to send message: Unknown error", true);
                }
            }
        }
    };
}

// Add event listener to the "Start Session" button
document.getElementById("startSessionButton")?.addEventListener("click", startSession);