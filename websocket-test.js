// Connect to the Socket.IO server with WebSocket as the only transport
const socket = io("http://localhost:5000", {
    transports: ["websocket"]
});

// Listen for the 'connect' event
socket.on("connect", () => {
    console.log("Connected to the server using WebSocket transport");

    // Send a test event to the server
    socket.emit("message", { text: "Hello from the browser console!" });
});

// Listen for a custom event from the server (replace 'message' with your event name)
socket.on("message", (data) => {
    console.log("Received message from server:", data);
});

// Listen for the 'disconnect' event
socket.on("disconnect", () => {
    console.log("Disconnected from the server");
});

// Function to send additional messages to the server
function sendMessage(event, data) {
    socket.emit(event, data);
    console.log(`Sent event '${event}' with data:`, data);
}
