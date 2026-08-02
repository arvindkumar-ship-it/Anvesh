// 'use client';

// import { useEffect, useState } from 'react';
// import { useCallback } from 'react';
// // Is hook file mein sabse upar ye import add kar:
// import { io, Socket } from 'socket.io-client';

// // Aur useRealtimeSocket function ke andar, pehli line par socket state bana:
// export function useRealtimeSocket(config: RealtimeConfig = {}) {
//   const [socket, setSocket] = useState<Socket | null>(null); // Ye add kar
//   const [isConnected, setIsConnected] = useState(false);
//   // ... baaki code

// interface RealtimeConfig {
//   endpoint?: string;
//   autoConnect?: boolean;
// }

// interface SocketMessage {
//   type: 'step_update' | 'log_entry' | 'drill_status' | 'code_update';
//   data: any;
//   timestamp: number;
// }

// /**
//  * Custom hook for Socket.io integration
//  * Since Socket.io requires a backend, this provides the structure
//  * and can be easily connected to your backend
//  */
// export function useRealtimeSocket(config: RealtimeConfig = {}) {
//   const [isConnected, setIsConnected] = useState(false);
//   const [messages, setMessages] = useState<SocketMessage[]>([]);
//   const [error, setError] = useState<string | null>(null);

//   // Initialize socket connection
//   useEffect(() => {
//     const connectSocket = async () => {
//       try {
//         // In a real implementation, you would import and initialize Socket.io here
//         // import io from 'socket.io-client';
//         // const socket = io(config.endpoint || process.env.NEXT_PUBLIC_SOCKET_URL);
        
//         // For now, we simulate the connection
//         setIsConnected(true);
        
//         // Setup event listeners would go here
//         // socket.on('step_update', handleStepUpdate);
//         // socket.on('log_entry', handleLogEntry);
//         // etc.
        
//       } catch (err) {
//         setError(err instanceof Error ? err.message : 'Connection failed');
//         setIsConnected(false);
//       }
//     };

//     if (config.autoConnect !== false) {
//       connectSocket();
//     }

//     return () => {
//       // Cleanup socket connection
//       setIsConnected(false);
//     };
//   }, [config]);

//   const emit = useCallback((type: SocketMessage['type'], data: any) => {
//     const message: SocketMessage = {
//       type,
//       data,
//       timestamp: Date.now(),
//     };
//     setMessages(prev => [...prev, message]);
    
//     // In a real implementation:
//     // socket.emit('message', message);
//   }, []);

//   return {
//     isConnected,
//     messages,
//     error,
//     emit,
//   };
// }

// /**
//  * Hook to listen for step updates
//  */
// export function useStepUpdates() {
//   const [currentStep, setCurrentStep] = useState(1);
//   const [stepHistory, setStepHistory] = useState<number[]>([]);

//   const handleStepUpdate = useCallback((newStep: number) => {
//     setCurrentStep(newStep);
//     setStepHistory(prev => [...prev, newStep]);
//   }, []);

//   return { currentStep, stepHistory, handleStepUpdate };
// }

// /**
//  * Hook to listen for log entries
//  */
// export function useLogStream() {
//   const [logs, setLogs] = useState<any[]>([]);
//   const [maxLogs] = useState(100);

//   const addLog = useCallback((logEntry: any) => {
//     setLogs(prev => {
//       const updated = [...prev, logEntry];
//       return updated.slice(-maxLogs);
//     });
//   }, [maxLogs]);

//   const clearLogs = useCallback(() => {
//     setLogs([]);
//   }, []);

//   return { logs, addLog, clearLogs };
// }

// /**
//  * Hook to listen for security drill updates
//  */
// export function useDrillUpdates() {
//   const [drillStatus, setDrillStatus] = useState<Map<string, boolean>>(new Map());

//   const updateDrill = useCallback((drillId: string, isHardened: boolean) => {
//     setDrillStatus(prev => new Map(prev).set(drillId, isHardened));
//   }, []);

//   return { drillStatus, updateDrill };
// }

// /**
//  * Configuration for Socket.io backend
//  * This should be called on your backend to setup the server
//  */
// export const SOCKET_EVENTS = {
//   // Client -> Server
//   CONNECT: 'connect',
//   DISCONNECT: 'disconnect',
//   START_AUDIT: 'start_audit',
//   PAUSE_AUDIT: 'pause_audit',
//   RESUME_AUDIT: 'resume_audit',
  
//   // Server -> Client
//   STEP_UPDATE: 'step_update',
//   LOG_ENTRY: 'log_entry',
//   DRILL_UPDATE: 'drill_update',
//   CODE_UPDATE: 'code_update',
//   FALLBACK_ALERT: 'fallback_alert',
//   AUDIT_COMPLETE: 'audit_complete',
//   ERROR: 'error',
// } as const;




'use client';

import { useEffect, useState, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';
// File ke top par, imports ke baad
let globalSocket: Socket | null = null;

interface RealtimeConfig {
  endpoint?: string;
  autoConnect?: boolean;
}

interface SocketMessage {
  // Yahan 'audit_complete' add karo
  type: 'step_update' | 'log_entry' | 'drill_status' | 'code_update' | 'start_audit' | 'start_pipeline' | 'audit_complete'; 
  data: any;
  timestamp: number;
}

/**
 * Custom hook for Socket.io integration
 */
// export function useRealtimeSocket(config: RealtimeConfig = {}) {
//   const [socket, setSocket] = useState<Socket | null>(null);
//   const [isConnected, setIsConnected] = useState(false);
//   const [messages, setMessages] = useState<SocketMessage[]>([]);
//   const [error, setError] = useState<string | null>(null);

//   // Initialize socket connection
//   useEffect(() => {
//     const connectSocket = async () => {
//       try {
//         // Step 1: Real Connection setup
//         const socketInstance = io(config.endpoint || 'http://localhost:8000', {
//           transports: ['websocket'],
//           autoConnect: config.autoConnect !== false
//         });

//         socketInstance.on('connect', () => {
//           setIsConnected(true);
//           console.log('Connected to Backend');
//         });

//         socketInstance.on('disconnect', () => {
//           setIsConnected(false);
//         });
//         // lib/realtime-socket.js ke andar jaha socket.on lagaye hain
//         socketInstance.on('audit_complete', (data) => {
//               // Ye event backend se report layega
//               window.dispatchEvent(new CustomEvent('hermes_report_ready', { detail: data.report }));
//         });

//         setSocket(socketInstance);
//         // Aur uske THEEK NICHE ye paste kar do:
//         socketInstance.on('log_entry', (data) => {
//           const newMsg: SocketMessage = {
//           type: 'log_entry',
//           data: data,
//           timestamp: Date.now()
//           };
//           setMessages(prev => [...prev, newMsg]);
//         });

// socketInstance.on('step_update', (data) => {
//   const newMsg: SocketMessage = {
//     type: 'step_update',
//     data: data,
//     timestamp: Date.now()
//   };
//   setMessages(prev => [...prev, newMsg]);
// });
        
//       } catch (err) {
//         setError(err instanceof Error ? err.message : 'Connection failed');
//         setIsConnected(false);
//       }
//     };

//     if (config.autoConnect !== false) {
//       connectSocket();
//     }

//     return () => {
//       if (socket) socket.disconnect();
//     };
//   }, [config.endpoint, config.autoConnect]);

//   // const emit = useCallback((type: SocketMessage['type'], data: any) => {
//   //   if (socket) {
//   //     socket.emit(type, data);
//   //   }
    
//   //   const message: SocketMessage = {
//   //     type,
//   //     data,
//   //     timestamp: Date.now(),
//   //   };
//   //   setMessages(prev => [...prev, message]);
//   // }, [socket]);
//   const emit = useCallback((type: SocketMessage['type'], data: any) => {
//     console.log('Emitting:', type, 'Socket:', socket?.id); // add this
//     if (socket) {
//       socket.emit(type, data);
//     }
//     const message: SocketMessage = {
//       type,
//       data,
//       timestamp: Date.now(),
//     };
//     setMessages(prev => [...prev, message]);
//   }, [socket]);
//   return {
//     socket,
//     isConnected,
//     messages,
//     error,
//     emit,
//   };
// }
export function useRealtimeSocket(config: RealtimeConfig = {}) {
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState<SocketMessage[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // 1. Singleton Check: Ek baar hi socket banega
    if (!globalSocket) {
      globalSocket = io(config.endpoint || 'http://localhost:8000', {
        transports: ['websocket'],
        reconnectionAttempts: 5,
        timeout: 120000, 
      });
    }

    const s = globalSocket;

    // 2. Event Listeners
    const onConnect = () => setIsConnected(true);
    const onDisconnect = () => setIsConnected(false);
    
    // Generic message handler taaki hooks sync mein rahein
    const handleMessage = (type: SocketMessage['type'], data: any) => {
      setMessages(prev => [...prev, { type, data, timestamp: Date.now() }]);
    };

    s.on('connect', onConnect);
    s.on('disconnect', onDisconnect);
    s.on('log_entry', (data) => handleMessage('log_entry', data));
    s.on('step_update', (data) => handleMessage('step_update', data));
    s.on('audit_complete', (data) => handleMessage('audit_complete', data));

    // 3. Cleanup: Listeners off karo, socket disconnect nahi
    return () => {
      s.off('connect', onConnect);
      s.off('disconnect', onDisconnect);
      s.off('log_entry');
      s.off('step_update');
      s.off('audit_complete');
    };
  }, [config.endpoint]);

  const emit = useCallback((type: string, data: any) => {
    if (globalSocket?.connected) {
      globalSocket.emit(type, data);
    } else {
      console.error("Hermes Socket not connected!");
    }
  }, []);

  return { isConnected, messages, error, emit };
}

/**
 * Hook to listen for step updates
 */
/**
 * Hook to listen for step updates from Socket
 */
export function useStepUpdates() {
  const { messages } = useRealtimeSocket(); // Socket se messages lo
  const [currentStep, setCurrentStep] = useState(1);
  const [stepHistory, setStepHistory] = useState<number[]>([]);

  useEffect(() => {
    // Sirf 'step_update' wale messages filter karo
    const latestStepMsg = messages.filter(m => m.type === 'step_update').pop();
    
    if (latestStepMsg && latestStepMsg.data.step) {
      const newStep = latestStepMsg.data.step;
      setCurrentStep(newStep);
      setStepHistory(prev => {
        // Duplicate steps na add hon history mein
        if (prev.includes(newStep)) return prev;
        return [...prev, newStep];
      });
    }
  }, [messages]);

  return { currentStep, stepHistory };
}

/**
 * Hook to listen for log entries
 */
/**
 * Hook to listen for log entries from Socket
 */
export function useLogStream() {
  const { messages } = useRealtimeSocket(); // Socket se messages lo
  const [logs, setLogs] = useState<any[]>([]);
  const [maxLogs] = useState(100);

  useEffect(() => {
    // Sirf 'log_entry' wale messages filter karo
    const latestLog = messages.filter(m => m.type === 'log_entry').pop();
    
    if (latestLog) {
      setLogs(prev => {
        // Unique ID fix taaki React warning na de
        const uniqueLog = {
          ...latestLog.data,
          id: latestLog.data.id || `${Date.now()}-${Math.random()}`
        };
        // Naya log add karo aur limit rakho
        const updated = [...prev, uniqueLog];
        return updated.slice(-maxLogs);
      });
    }
  }, [messages, maxLogs]);

  const clearLogs = useCallback(() => {
    setLogs([]);
  }, []);

  return { logs, clearLogs };
}

/**
 * Hook to listen for security drill updates
 */
export function useDrillUpdates() {
  const [drillStatus, setDrillStatus] = useState<Map<string, boolean>>(new Map());

  const updateDrill = useCallback((drillId: string, isHardened: boolean) => {
    setDrillStatus(prev => new Map(prev).set(drillId, isHardened));
  }, []);

  return { drillStatus, updateDrill };
}

export const SOCKET_EVENTS = {
  CONNECT: 'connect',
  DISCONNECT: 'disconnect',
  START_AUDIT: 'start_audit',
  PAUSE_AUDIT: 'pause_audit',
  RESUME_AUDIT: 'resume_audit',
  STEP_UPDATE: 'step_update',
  LOG_ENTRY: 'log_entry',
  DRILL_UPDATE: 'drill_update',
  CODE_UPDATE: 'code_update',
  FALLBACK_ALERT: 'fallback_alert',
  AUDIT_COMPLETE: 'audit_complete',
  ERROR: 'error',
} as const;