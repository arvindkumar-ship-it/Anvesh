// 'use client';

// import React, { useState, useEffect, useRef } from 'react';
// import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

// interface LogEntry {
//   id: string;
//   timestamp: string;
//   type: 'info' | 'error' | 'success' | 'warning';
//   message: string;
// }

// const SAMPLE_LOGS: LogEntry[] = [];

// interface TerminalLogViewerProps {
//   logs?: LogEntry[];
//   isLive?: boolean;
// }

// export function TerminalLogViewer({ logs = SAMPLE_LOGS, isLive = true }: TerminalLogViewerProps) {
//   const [displayLogs, setDisplayLogs] = useState<LogEntry[]>(logs);
//   const [autoScroll, setAutoScroll] = useState(true);
//   const scrollRef = useRef<HTMLDivElement>(null);
//   const contentRef = useRef<HTMLDivElement>(null);

//   useEffect(() => {
//     if (autoScroll && scrollRef.current) {
//       scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
//     }
//   }, [displayLogs, autoScroll]);

//   useEffect(() => {
//     if (!isLive) return;

//     const newLogMessages = [
//       { id: `${Date.now()}`, timestamp: new Date().toLocaleTimeString(), type: 'info' as const, message: '[INFO] Step 7: Adversarial testing in progress...' },
//       { id: `${Date.now() + 1}`, timestamp: new Date().toLocaleTimeString(), type: 'warning' as const, message: '[!] Attempting injection attacks' },
//       { id: `${Date.now() + 2}`, timestamp: new Date().toLocaleTimeString(), type: 'success' as const, message: '[✓] Defense mechanism activated' },
//     ];

//     const timer = setInterval(() => {
//       setDisplayLogs(prev => {
//         const updated = [...prev, newLogMessages[Math.floor(Math.random() * newLogMessages.length)]];
//         return updated.slice(-50); // Keep only last 50 logs
//       });
//     }, 2000);

//     return () => clearInterval(timer);
//   }, [isLive]);

//   const getLogColor = (type: string) => {
//     switch (type) {
//       case 'error': return 'text-red-400';
//       case 'success': return 'text-green-400';
//       case 'warning': return 'text-yellow-400';
//       default: return 'text-cyan-400';
//     }
//   };

//   return (
//     <Card className="bg-card border-border">
//       <CardHeader className="pb-3 border-b border-border">
//         <div className="flex items-center justify-between">
//           <CardTitle className="text-sm font-semibold">Logs</CardTitle>
//           <div className="flex gap-2">
//             <button
//               onClick={() => setAutoScroll(!autoScroll)}
//               className="text-xs px-2 py-1 bg-muted/20 hover:bg-muted/30 rounded-lg text-muted-foreground transition-colors"
//             >
//               {autoScroll ? 'Auto' : 'Manual'}
//             </button>
//             <button
//               onClick={() => setDisplayLogs([])}
//               className="text-xs px-2 py-1 bg-muted/20 hover:bg-muted/30 rounded-lg text-muted-foreground transition-colors"
//             >
//               Clear
//             </button>
//           </div>
//         </div>
//       </CardHeader>
//       <CardContent className="pt-3">
//         <div
//           ref={scrollRef}
//           className="bg-black/30 border border-border rounded-lg p-3 font-mono text-xs h-64 overflow-y-auto"
//         >
//           <div ref={contentRef} className="space-y-1">
//             {displayLogs.length === 0 ? (
//               <div className="text-muted-foreground/50">
//                 Waiting for logs...
//               </div>
//             ) : (
//               displayLogs.map((log, index) => (
//               <div key={`${log.id}-${index}`} className="fade-in">
//                   <span className="text-muted-foreground/70">[{log.timestamp}]</span>{' '}
//                   <span className={getLogColor(log.type)}>{log.message}</span>
//                 </div>
//               ))
//             )}
//             {isLive && displayLogs.length > 0 && (
//               <div className="text-primary status-indicator">
//                 <span className="inline-block w-1 h-3 bg-primary"></span>
//               </div>
//             )}
//           </div>
//         </div>
//         <div className="mt-3 flex justify-between items-center text-xs text-muted-foreground">
//           <span>{displayLogs.length} entries</span>
//           {isLive && (
//             <div className="flex items-center gap-2">
//               <div className="w-2 h-2 bg-green-500 rounded-full status-indicator"></div>
//               <span>Live</span>
//             </div>
//           )}
//         </div>
//       </CardContent>
//     </Card>
//   );
// }


'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface LogEntry {
  id: string;
  timestamp: string;
  type: 'info' | 'error' | 'success' | 'warning';
  message: string;
}

const SAMPLE_LOGS: LogEntry[] = [];

interface TerminalLogViewerProps {
  logs?: LogEntry[];
  isLive?: boolean;
}

export function TerminalLogViewer({ logs = SAMPLE_LOGS, isLive = true }: TerminalLogViewerProps) {
  // Syncing displayLogs with incoming props instead of local state only
  const [displayLogs, setDisplayLogs] = useState<LogEntry[]>(logs);
  const [autoScroll, setAutoScroll] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  // REAL-TIME SYNC: Update display when props change
  useEffect(() => {
    setDisplayLogs(logs);
  }, [logs]);

  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [displayLogs, autoScroll]);

  // BRUTAL CLEANUP: Dummy setInterval removed, only tracking isLive status now
  useEffect(() => {
    if (!isLive) return;
    // No more fake timers here. Data comes from props.
  }, [isLive]);

  const getLogColor = (type: string) => {
    switch (type) {
      case 'error': return 'text-red-400';
      case 'success': return 'text-green-400';
      case 'warning': return 'text-yellow-400';
      default: return 'text-cyan-400';
    }
  };

  return (
    <Card className="bg-card border-border">
      <CardHeader className="pb-3 border-b border-border">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-semibold">Logs</CardTitle>
          <div className="flex gap-2">
            <button
              onClick={() => setAutoScroll(!autoScroll)}
              className="text-xs px-2 py-1 bg-muted/20 hover:bg-muted/30 rounded-lg text-muted-foreground transition-colors"
            >
              {autoScroll ? 'Auto' : 'Manual'}
            </button>
            <button
              onClick={() => setDisplayLogs([])}
              className="text-xs px-2 py-1 bg-muted/20 hover:bg-muted/30 rounded-lg text-muted-foreground transition-colors"
            >
              Clear
            </button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-3">
        <div
          ref={scrollRef}
          className="bg-black/30 border border-border rounded-lg p-3 font-mono text-xs h-64 overflow-y-auto"
        >
          <div ref={contentRef} className="space-y-1">
            {displayLogs.length === 0 ? (
              <div className="text-muted-foreground/50">
                Waiting for logs...
              </div>
            ) : (
              displayLogs.map((log, index) => (
                <div key={`${log.id}-${index}`} className="fade-in">
                  {/* Backend might send 'level' or 'msg', so we use conditional fallback */}
                  <span className="text-muted-foreground/70">[{log.timestamp || new Date().toLocaleTimeString()}]</span>{' '}
                  <span className={getLogColor(log.type || (log as any).level)}>
                    {log.message || (log as any).msg}
                  </span>
                </div>
              ))
            )}
            {isLive && displayLogs.length > 0 && (
              <div className="text-primary status-indicator">
                <span className="inline-block w-1 h-3 bg-primary"></span>
              </div>
            )}
          </div>
        </div>
        <div className="mt-3 flex justify-between items-center text-xs text-muted-foreground">
          <span>{displayLogs.length} entries</span>
          {isLive && (
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full status-indicator"></div>
              <span>Live</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}