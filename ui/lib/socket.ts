import { io } from "socket.io-client";

// Backend URL - port 8000 jahan tera app.py chal raha hai
const SOCKET_URL = "http://localhost:8000";

export const socket = io(SOCKET_URL, {
  autoConnect: false,      // Hum isse manually connect karenge page load par
  transports: ["websocket"], // Faster than polling
  reconnectionAttempts: 5,
});