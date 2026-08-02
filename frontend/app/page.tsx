// 'use client';

// import React, { useState, useEffect } from 'react';
// import { LiveStatusSidebar } from '@/components/live-status-sidebar';
// import { TerminalLogViewer } from '@/components/terminal-log-viewer';
// import { SecurityDrillGrid } from '@/components/security-drill-grid';
// import { CodeDiffViewer } from '@/components/code-diff-viewer';
// import { Card, CardContent } from '@/components/ui/card';
// import { useLogStream, useStepUpdates, useRealtimeSocket } from "@/lib/realtime-socket";
// import { interval } from 'date-fns/interval';
// export default function Dashboard() {
//   // const [currentStep, setCurrentStep] = useState(1);
//   const [fallbackAlert, setFallbackAlert] = useState<string | undefined>(undefined);
//   // Ye asli data hooks hain
//   const { isConnected, emit } = useRealtimeSocket();
//   const { logs } = useLogStream();
//   const [targetUrl, setTargetUrl] = useState('');
//   const [reportData, setReportData] = useState<string | null>(null);
//   const handleStartAudit = () => {
//   if (isConnected) {
//     // emit('start_audit', { target: 'http://localhost:8000' });
//     emit('start_pipeline', { url: targetUrl, task: 'Generate hardened production code' });
//     console.log("Audit Signal Sent!");
//   } else {
//     alert("Backend connected nahi hai, pehle server check kar!");
//   }
// };
//   const { currentStep } = useStepUpdates();
//   // return () => clearInterval(interval);
//   const downloadReport = () => {
//   if (!reportData) return;
//   const blob = new Blob([reportData], { type: 'text/plain' });
//   const url = URL.createObjectURL(blob);
//   const a = document.createElement('a');
//   a.href = url;
//   a.download = `Hermes_Security_Report_${new Date().getTime()}.txt`;
//   a.click();
//   URL.revokeObjectURL(url);
// };
// useEffect(() => {
//   const handleReport = (e: any) => {
//     console.log("📥 Report Received!");
//     setReportData(e.detail);
//   };
//   window.addEventListener('hermes_report_ready', handleReport);
//   return () => window.removeEventListener('hermes_report_ready', handleReport);
// }, []);

//   return (
//     <div className="flex h-screen bg-background overflow-hidden">
//       {/* Sidebar */}
//       <LiveStatusSidebar 
//         currentStep={currentStep} 
//         fallbackAlert={fallbackAlert}
//       />

//       {/* Main Content */}
//       <div className="flex-1 flex flex-col overflow-hidden">
//         {/* Header */}
//         <div className="border-b border-border bg-card px-8 py-4">
//           <h1 className="text-2xl font-semibold">Agentic AI Security Audit</h1>
//           <p className="text-sm text-muted-foreground mt-1">Real-time monitoring of security hardening</p>
//           <div className="mt-3 flex gap-6 text-sm">
//             <div className="flex items-center gap-2">
//               <div className="w-2 h-2 bg-green-500 rounded-full status-indicator"></div>
//               <span>Step: <span className="font-medium">{currentStep}/10</span></span>
//             </div>
//             <div className="flex items-center gap-2">
//               <div className="w-2 h-2 bg-primary rounded-full status-indicator"></div>
//               <span>Status: <span className="font-medium">Running</span></span>
//             </div>
//           </div>
//         </div>

//         {/* Content Area */}
//         <div className="flex-1 overflow-y-auto">
//           <div className="p-8 space-y-8">
//             {/* Terminal and Security Grid Row */}
//             <div className="grid grid-cols-3 gap-6">
//               {/* Terminal (spans 1 column) */}
//               <div className="col-span-2">
//                 <TerminalLogViewer logs={logs} isLive={isConnected} />
//               </div>
//               {/* Status Card (spans 1 column) */}
//               <div className="space-y-4">
//                 <input
//                     type="text"
//                     placeholder="Enter API URL..."
//                     value={targetUrl}
//                     onChange={(e) => setTargetUrl(e.target.value)}
//                     className="w-full px-4 py-3 rounded-xl bg-gray-900 border border-gray-700 text-white text-sm placeholder-gray-500 focus:outline-none focus:border-blue-500"
//                   />
              
//                 {/* ⬇️ START AUDIT BUTTON (Paste from here) ⬇️ */}
//                 <button
//                   onClick={handleStartAudit}
//                   disabled={!isConnected}
//                   className={`w-full py-4 rounded-xl font-bold text-sm transition-all duration-300 shadow-lg active:scale-95 ${
//                     isConnected 
//                       ? "bg-blue-600 text-white hover:bg-blue-700 shadow-blue-500/20" 
//                       : "bg-gray-800 text-gray-500 cursor-not-allowed"
//                   }`}
//                 >
//                   {isConnected ? '🚀 START SECURITY AUDIT' : '⏳ WAITING FOR BACKEND...'}
//                 </button>
//                 {/* ⬆️ BUTTON END ⬆️ */}
//                 <Card className="bg-card border-border">
//                   <CardContent className="p-4">
//                     <h3 className="text-sm font-medium mb-3">Status</h3>
//                     <div className="space-y-3">
//                       <div>
//                         <div className="text-xs text-muted-foreground">Active</div>
//                         <div className="text-xl font-semibold text-primary mt-1">{currentStep}</div>
//                       </div>
//                       <div className="h-px bg-border"></div>
//                       <div>
//                         <div className="text-xs text-muted-foreground">Progress</div>
//                         <div className="text-xl font-semibold text-green-500 mt-1">{Math.round((currentStep / 10) * 100)}%</div>
//                       </div>
//                       <div className="h-px bg-border"></div>
//                       <div>
//                         <div className="text-xs text-muted-foreground">Done</div>
//                         <div className="text-xl font-semibold text-primary mt-1">{currentStep - 1}</div>
//                       </div>
//                     </div>
//                   </CardContent>
//                 </Card>

//                 {/* Quick Stats */}
//                 <Card className="bg-card border-border">
//                   <CardContent className="p-4">
//                     <h3 className="text-sm font-medium mb-3">Info</h3>
//                     <div className="space-y-2 text-xs text-muted-foreground">
//                       <div className="flex justify-between">
//                         <span>Latency</span>
//                         <span className="text-foreground">42ms</span>
//                       </div>
//                       <div className="flex justify-between">
//                         <span>Provider</span>
//                         <span className="text-foreground">{currentStep >= 6 ? 'Groq' : 'Gemini'}</span>
//                       </div>
//                       <div className="flex justify-between">
//                         <span>Errors</span>
//                         <span className="text-foreground">0</span>
//                       </div>
//                     </div>
//                   </CardContent>
//                 </Card>
//               </div>
//             </div>

//             {/* Security Drill Grid */}
//             <SecurityDrillGrid step={currentStep} />

//             {/* Code Diff Viewer */}
//             {currentStep >= 7 && <CodeDiffViewer />}

//             {/* Bottom Info */}
//             <div className="bg-card border border-border rounded-lg p-4">
//               <h3 className="text-sm font-medium mb-2">Step Info</h3>
//               <p className="text-sm text-muted-foreground">
//                 {currentStep === 1 && 'Threat analysis - identifying vulnerabilities'}
//                 {currentStep === 2 && 'Defense code generation'}
//                 {currentStep === 3 && 'Code validation'}
//                 {currentStep === 4 && 'Security scanning'}
//                 {currentStep === 5 && 'Attack simulation'}
//                 {currentStep === 6 && 'Failure detection'}
//                 {currentStep === 7 && 'Adversarial testing'}
//                 {currentStep === 8 && 'Code hardening'}
//                 {currentStep === 9 && 'Final validation'}
//                 {currentStep === 10 && 'Deployment ready'}
//               </p>
//             </div>
//           </div>
//         </div>
//       </div>
//     </div>
//   );
// }
// // // 1. State ke niche (Line 18 ke paas)
// // const [reportData, setReportData] = useState(null);

// // // 2. Report receive karne ke liye listener
// // useEffect(() => {
// //   const handleReport = (e) => {
// //     setReportData(e.detail);
// //   };
// //   window.addEventListener('hermes_report_ready', handleReport);
// //   return () => window.removeEventListener('hermes_report_ready', handleReport);
// // }, []);

// // // 3. Download function
// // const downloadReport = () => {
// //   if (!reportData) return;
// //   const blob = new Blob([reportData], { type: 'text/plain' });
// //   const url = URL.createObjectURL(blob);
// //   const a = document.createElement('a');
// //   a.href = url;
// //   a.download = `Hermes_Security_Report_${new Date().getTime()}.txt`;
// //   a.click();
// // };











// 'use client';

// import React, { useState, useEffect } from 'react';
// import { LiveStatusSidebar } from '@/components/live-status-sidebar';
// import { TerminalLogViewer } from '@/components/terminal-log-viewer';
// import { SecurityDrillGrid } from '@/components/security-drill-grid';
// import { CodeDiffViewer } from '@/components/code-diff-viewer';
// import { Card, CardContent } from '@/components/ui/card';
// import { useLogStream, useStepUpdates, useRealtimeSocket } from "@/lib/realtime-socket";

// export default function Dashboard() {
//   const [fallbackAlert, setFallbackAlert] = useState<string | undefined>(undefined);
//   const { isConnected, emit } = useRealtimeSocket();
//   const { logs } = useLogStream();
//   const [targetUrl, setTargetUrl] = useState('');
//   const [reportData, setReportData] = useState<string | null>(null);
//   const { currentStep } = useStepUpdates();

//   const handleStartAudit = () => {
//     if (isConnected) {
//       setReportData(null); 
//       emit('start_pipeline', { url: targetUrl, task: 'Generate hardened production code' });
//       console.log("Audit Signal Sent!");
//     } else {
//       alert("Backend connected nahi hai, pehle server check kar!");
//     }
//   };

//   const downloadReport = () => {
//     if (!reportData) return;
//     const blob = new Blob([reportData], { type: 'text/plain' });
//     const url = URL.createObjectURL(blob);
//     const a = document.createElement('a');
//     a.href = url;
//     a.download = `Hermes_Security_Report_${new Date().getTime()}.txt`;
//     document.body.appendChild(a);
//     a.click();
//     document.body.removeChild(a);
//     URL.revokeObjectURL(url);
//   };

//   useEffect(() => {
//     const handleReport = (e: any) => {
//       console.log("📥 Report Received!");
//       setReportData(e.detail);
//     };
//     window.addEventListener('hermes_report_ready', handleReport);
//     return () => window.removeEventListener('hermes_report_ready', handleReport);
//   }, []);

//   return (
//     <div className="flex h-screen bg-background overflow-hidden relative">
//       <LiveStatusSidebar 
//         currentStep={currentStep} 
//         fallbackAlert={fallbackAlert}
//       />

//       <div className="flex-1 flex flex-col overflow-hidden">
//         <div className="border-b border-border bg-card px-8 py-4">
//           <h1 className="text-2xl font-semibold">Agentic AI Security Audit</h1>
//           <p className="text-sm text-muted-foreground mt-1">Real-time monitoring of security hardening</p>
//           <div className="mt-3 flex gap-6 text-sm">
//             <div className="flex items-center gap-2">
//               <div className="w-2 h-2 bg-green-500 rounded-full"></div>
//               <span>Step: <span className="font-medium">{currentStep}/10</span></span>
//             </div>
//             <div className="flex items-center gap-2">
//               <div className="w-2 h-2 bg-primary rounded-full"></div>
//               <span>Status: <span className="font-medium">Running</span></span>
//             </div>
//           </div>
//         </div>

//         <div className="flex-1 overflow-y-auto">
//           <div className="p-8 space-y-8">
//             <div className="grid grid-cols-3 gap-6">
//               <div className="col-span-2">
//                 <TerminalLogViewer logs={logs} isLive={isConnected} />
//               </div>
//               <div className="space-y-4">
//                 <input
//                     type="text"
//                     placeholder="Enter API URL..."
//                     value={targetUrl}
//                     onChange={(e) => setTargetUrl(e.target.value)}
//                     className="w-full px-4 py-3 rounded-xl bg-gray-900 border border-gray-700 text-white text-sm focus:outline-none focus:border-blue-500"
//                   />
//                 <button
//                   onClick={handleStartAudit}
//                   disabled={!isConnected}
//                   className={`w-full py-4 rounded-xl font-bold text-sm transition-all duration-300 shadow-lg active:scale-95 ${
//                     isConnected 
//                       ? "bg-blue-600 text-white hover:bg-blue-700 shadow-blue-500/20" 
//                       : "bg-gray-800 text-gray-500 cursor-not-allowed"
//                   }`}
//                 >
//                   {isConnected ? '🚀 START SECURITY AUDIT' : '⏳ WAITING FOR BACKEND...'}
//                 </button>
//                 <Card className="bg-card border-border">
//                   <CardContent className="p-4">
//                     <h3 className="text-sm font-medium mb-3">Status</h3>
//                     <div className="space-y-3">
//                       <div>
//                         <div className="text-xs text-muted-foreground">Progress</div>
//                         <div className="text-xl font-semibold text-green-500 mt-1">{Math.round((currentStep / 10) * 100)}%</div>
//                       </div>
//                       <div className="h-px bg-border"></div>
//                       <div>
//                         <div className="text-xs text-muted-foreground">Done</div>
//                         <div className="text-xl font-semibold text-primary mt-1">{currentStep - 1}</div>
//                       </div>
//                     </div>
//                   </CardContent>
//                 </Card>
//               </div>
//             </div>

//             <SecurityDrillGrid step={currentStep} />
//             {currentStep >= 7 && <CodeDiffViewer />}

//             <div className="bg-card border border-border rounded-lg p-4">
//               <h3 className="text-sm font-medium mb-2">Step Info</h3>
//               <p className="text-sm text-muted-foreground">
//                 {currentStep === 10 ? 'Audit complete. Deployment ready.' : 'Processing security audit...'}
//               </p>
//             </div>
//           </div>
//         </div>
//       </div>

//       {/* 🆕 FLOATING BUTTON: Zero grid impact, strictly separate */}
//       {reportData && (
//         <div className="fixed bottom-8 right-8 z-[9999]">
//           <button
//             onClick={downloadReport}
//             className="group flex items-center justify-center w-14 h-14 bg-green-600 hover:w-48 rounded-full transition-all duration-300 shadow-2xl text-white overflow-hidden active:scale-90 border border-green-400"
//           >
//             <span className="text-xl">📥</span>
//             <span className="max-w-0 group-hover:max-w-xs transition-all duration-300 ml-0 group-hover:ml-2 whitespace-nowrap font-bold text-xs uppercase">
//               Download Report
//             </span>
//           </button>
//         </div>
//       )}
//     </div>
//   );
// }











'use client';

import React, { useState, useEffect } from 'react';
import { LiveStatusSidebar } from '@/components/live-status-sidebar';
import { TerminalLogViewer } from '@/components/terminal-log-viewer';
import { SecurityDrillGrid } from '@/components/security-drill-grid';
import { CodeDiffViewer } from '@/components/code-diff-viewer';
import { Card, CardContent } from '@/components/ui/card';
import { useLogStream, useStepUpdates, useRealtimeSocket } from "@/lib/realtime-socket";

export default function Dashboard() {
  const { isConnected, emit, messages } = useRealtimeSocket(); 
  
  const { logs } = useLogStream();
  const { currentStep } = useStepUpdates();
  const [targetUrl, setTargetUrl] = useState('');
  const [reportData, setReportData] = useState<string | null>(null);

  // 1. Report Listener (Bina UI ko hile data capture karega)
  useEffect(() => {
    if (messages.length === 0) return;

    // Socket messages mein 'audit_complete' dhoondo
    const completeMsg = messages.find((m: any) => m.type === 'audit_complete');
    
    if (completeMsg && !reportData) {
      console.log("✅ Report captured from socket!");
      // Backend 'report' key mein data bhej raha hai
      setReportData(completeMsg.data.report || completeMsg.data); 
    }
  }, [messages, reportData]);

  const downloadReport = () => {
    if (!reportData) return;
    const blob = new Blob([reportData], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Hermes_Report.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {/* Sidebar - Original */}
      <LiveStatusSidebar currentStep={currentStep} />

      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header - Original */}
        <div className="border-b border-border bg-card px-8 py-4">
          <h1 className="text-2xl font-semibold">Agentic AI Security Audit</h1>
          <div className="mt-3 flex gap-6 text-sm">
            <span>Step: <span className="font-medium text-green-500">{currentStep}/10</span></span>
            <span>Status:{" "}
              <span className={`font-medium ${currentStep === 10 || reportData ? 'text-green-500' : 'text-primary'}`}>
                {currentStep === 10 || reportData ? 'Completed' : 'Running'}
              </span>
            </span>
          </div>
        </div>

        {/* Responsive Content Area */}
        <div className="flex-1 overflow-y-auto p-8 space-y-8">
          <div className="grid grid-cols-3 gap-6">
            <div className="col-span-2">
              <TerminalLogViewer logs={logs} isLive={isConnected} />
            </div>

            <div className="space-y-4">
              <input
                type="text"
                value={targetUrl}
                onChange={(e) => setTargetUrl(e.target.value)}
                placeholder="Enter API URL..."
                className="w-full px-4 py-3 rounded-xl bg-gray-900 border border-gray-700 text-white outline-none"
              />
              <button
                onClick={() => emit('start_pipeline', { url: targetUrl, task: 'Harden code' })}
                disabled={!isConnected}
                className="w-full py-4 rounded-xl font-bold bg-blue-600 text-white hover:bg-blue-700 active:scale-95 transition-all"
              >
                {isConnected ? '🚀 START SECURITY AUDIT' : '⏳ WAITING...'}
              </button>

              {/* Status Display - Same as before */}
              <Card className="bg-card border-border p-4">
                <div className="text-xs text-muted-foreground uppercase tracking-wider">Progress</div>
                <div className="text-2xl font-bold text-green-500">{Math.round((currentStep / 10) * 100)}%</div>
              </Card>

              {/* Feature: Download Button (Only shows when ready) */}
              {reportData && (
                <button
                  onClick={downloadReport}
                  className="w-full py-4 rounded-xl font-bold bg-green-600 text-white shadow-lg animate-bounce border-2 border-green-400"
                >
                  📥 DOWNLOAD REPORT
                </button>
              )}
            </div>
          </div>

          <SecurityDrillGrid step={currentStep} />
          {currentStep >= 7 && <CodeDiffViewer />}
        </div>
      </div>
    </div>
  );
}