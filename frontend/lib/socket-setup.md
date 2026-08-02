/**
 * Socket.io Integration Guide
 * 
 * This file provides instructions for connecting the frontend to your backend
 */

// ============================================
// BACKEND SETUP (Node.js + Express + Socket.io)
// ============================================

// npm install socket.io cors

// In your backend (e.g., server.js or api/socket.js):
/*
const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const cors = require('cors');

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
  cors: {
    origin: process.env.FRONTEND_URL || 'http://localhost:3000',
    methods: ['GET', 'POST'],
  },
});

let currentStep = 1;
let auditRunning = false;

// Connection handling
io.on('connection', (socket) => {
  console.log('Client connected:', socket.id);
  
  // Send current state to newly connected client
  socket.emit('step_update', { step: currentStep });
  
  // Listen for audit control events
  socket.on('start_audit', () => {
    auditRunning = true;
    simulateAuditSteps(io);
  });
  
  socket.on('pause_audit', () => {
    auditRunning = false;
  });
  
  socket.on('disconnect', () => {
    console.log('Client disconnected:', socket.id);
  });
});

// Simulate audit steps
function simulateAuditSteps(io) {
  let step = 1;
  const stepInterval = setInterval(() => {
    if (!auditRunning) {
      clearInterval(stepInterval);
      return;
    }
    
    // Emit step update to all connected clients
    io.emit('step_update', { step });
    
    // Emit log entry
    io.emit('log_entry', {
      timestamp: new Date().toLocaleTimeString(),
      type: 'info',
      message: `Step ${step} in progress...`,
    });
    
    // Simulate fallback alert at step 6
    if (step === 6) {
      io.emit('fallback_alert', {
        message: 'Switching to Groq/8B',
        duration: 5000,
      });
    }
    
    // Emit drill updates from step 7
    if (step >= 7) {
      io.emit('drill_update', {
        drillId: String(Math.floor(Math.random() * 8) + 1),
        isHardened: step >= 8,
      });
    }
    
    step++;
    if (step > 10) {
      step = 1;
      io.emit('audit_complete', { message: 'Audit cycle complete' });
    }
  }, 4000);
}

server.listen(3001, () => {
  console.log('Socket.io server running on port 3001');
});
*/

// ============================================
// FRONTEND SETUP (.env.local)
// ============================================

/*
NEXT_PUBLIC_SOCKET_URL=http://localhost:3001
*/

// ============================================
// FRONTEND CLIENT SETUP (example)
// ============================================

// In your component or hook:
/*
import { useEffect, useState } from 'react';
import io from 'socket.io-client';

export function useAuditSocket() {
  const [socket, setSocket] = useState(null);
  const [currentStep, setCurrentStep] = useState(1);
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    const socketUrl = process.env.NEXT_PUBLIC_SOCKET_URL || 'http://localhost:3001';
    const newSocket = io(socketUrl);

    newSocket.on('connect', () => {
      console.log('Connected to socket server');
    });

    newSocket.on('step_update', (data) => {
      setCurrentStep(data.step);
    });

    newSocket.on('log_entry', (log) => {
      setLogs((prev) => [...prev, log].slice(-50));
    });

    newSocket.on('fallback_alert', (alert) => {
      // Handle fallback alert UI
      console.log(alert.message);
    });

    newSocket.on('disconnect', () => {
      console.log('Disconnected from socket server');
    });

    setSocket(newSocket);

    return () => newSocket.close();
  }, []);

  return { socket, currentStep, logs };
}
*/

// ============================================
// ALTERNATIVE: Using Vercel Serverless WebSockets
// ============================================

/*
If you prefer not to manage a separate Socket.io server,
consider using Vercel's WebSocket support or polling-based approach.

Option 1: Server-Sent Events (SSE)
- Simpler than WebSockets
- Built into most browsers
- No separate server needed

Option 2: API Polling
- Make periodic API calls to /api/audit-status
- Less real-time but easier to implement

Option 3: Vercel Functions + Third-party service
- Use Pusher.com or Supabase Realtime
- Zero server management
*/

export const SOCKET_CONFIG = {
  enabled: !!process.env.NEXT_PUBLIC_SOCKET_URL,
  url: process.env.NEXT_PUBLIC_SOCKET_URL || 'http://localhost:3001',
  reconnection: true,
  reconnectionDelay: 1000,
  reconnectionDelayMax: 5000,
  reconnectionAttempts: 5,
};
