// 'use client';

// import React, { useState, useEffect } from 'react';
// import { Card, CardContent } from '@/components/ui/card';
// // Top par import add karo
// import { useRealtimeSocket } from "@/lib/realtime-socket";

// export function SecurityDrillGrid({ step = 0 }: Security-drill-gridProps) {
//   const { messages } = useRealtimeSocket(); // Real-time messages lo
//   const [drills, setDrills] = useState<SecurityDrill[]>(SECURITY_DRILLS);
//   const [hardenProgress, setHardenProgress] = useState(0);

//   interface SecurityDrill {
//     id: string;
//     title: string;
//     description: string;
//     attackType: string;
//   vulnerable: boolean;
//   hardened: boolean;
// }

// const SECURITY_DRILLS: SecurityDrill[] = [
//   { id: '1', title: 'Rate Limiting', description: 'Request throttling attack', attackType: 'DoS', vulnerable: true, hardened: false },
//   { id: '2', title: 'Auth Bypass', description: 'Unauthorized access attempt', attackType: 'Auth', vulnerable: true, hardened: false },
//   { id: '3', title: 'Injection Attack', description: 'SQL/Code injection', attackType: 'Injection', vulnerable: true, hardened: false },
//   { id: '4', title: 'Data Leakage', description: 'Sensitive data exposure', attackType: 'Privacy', vulnerable: true, hardened: false },
//   { id: '5', title: 'Privilege Escalation', description: 'Unauthorized access elevation', attackType: 'Access', vulnerable: true, hardened: false },
//   { id: '6', title: 'CSRF Protection', description: 'Cross-site request forgery', attackType: 'Session', vulnerable: true, hardened: false },
//   { id: '7', title: 'Timeout Handling', description: 'Session expiration attacks', attackType: 'Session', vulnerable: true, hardened: false },
//   { id: '8', title: 'Input Validation', description: 'Malformed input handling', attackType: 'Validation', vulnerable: true, hardened: false },
// ];

// interface SecurityDrillGridProps {
//   step?: number;
// }

// export function SecurityDrillGrid({ step = 0 }: SecurityDrillGridProps) {
//   const [drills, setDrills] = useState<SecurityDrill[]>(SECURITY_DRILLS);
//   const [hardenProgress, setHardenProgress] = useState(0);

//   useEffect(() => {
//     // Simulate hardening process as steps progress (Step 8 onwards)
//     if (step >= 8) {
//       const progress = Math.min(100, (step - 8) * 12.5);
//       setHardenProgress(progress);
      
//       const hardenedCount = Math.floor((SECURITY_DRILLS.length * progress) / 100);
//       setDrills(prev => 
//         prev.map((drill, idx) => ({
//           ...drill,
//           hardened: idx < hardenedCount,
//           vulnerable: idx >= hardenedCount
//         }))
//       );
//     } else if (step >= 7) {
//       setHardenProgress(0);
//       // Show all as vulnerable during adversarial testing
//       setDrills(prev => prev.map(drill => ({ ...drill, vulnerable: true, hardened: false })));
//     }
//   }, [step]);

//   return (
//     <div className="space-y-4">
//       <div>
//         <h3 className="text-lg font-bold mb-2">Security Drill Results</h3>
//         <p className="text-sm text-muted-foreground mb-4">Real-time attack simulation and hardening status</p>
//       </div>

//       {/* Grid Container */}
//       <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
//         {drills.map((drill, idx) => (
//           <Card
//             key={drill.id}
//             className={`relative overflow-hidden border transition-all duration-300 ${
//               drill.hardened
//                 ? 'bg-green-500/10 border-green-500/30 shadow-sm hover:shadow-md'
//                 : drill.vulnerable
//                 ? 'bg-red-500/10 border-red-500/30 shadow-sm hover:shadow-md'
//                 : 'bg-muted/20 border-border'
//             }`}
//             style={{
//               animationDelay: `${idx * 50}ms`,
//             }}
//           >
//             <CardContent className="p-3">
//               <div className="space-y-2">
//                 <div className="flex items-start justify-between">
//                   <h4 className="font-medium text-sm leading-tight">{drill.title}</h4>
//                   {drill.hardened ? (
//                     <span className="text-lg fade-in">✓</span>
//                   ) : drill.vulnerable ? (
//                     <span className="text-lg status-indicator">⚠</span>
//                   ) : null}
//                 </div>
//                 <p className="text-xs text-muted-foreground">{drill.description}</p>
//                 <div className="flex gap-1 flex-wrap mt-2">
//                   <span className={`text-xs px-2 py-1 rounded-lg ${
//                     drill.hardened 
//                       ? 'bg-green-500/20 text-green-300'
//                       : drill.vulnerable
//                       ? 'bg-red-500/20 text-red-300'
//                       : 'bg-muted/50 text-muted-foreground'
//                   }`}>
//                     {drill.attackType}
//                   </span>
//                 </div>
//               </div>

//               {/* Bottom indicator line */}
//               <div className="absolute bottom-0 left-0 h-0.5 transition-all duration-300" 
//                 style={{
//                   background: drill.hardened 
//                     ? 'rgb(34, 197, 94)'
//                     : drill.vulnerable
//                     ? 'rgb(239, 68, 68)'
//                     : 'transparent',
//                   width: '100%'
//                 }}>
//               </div>
//             </CardContent>
//           </Card>
//         ))}
//       </div>

//       {/* Progress Bar */}
//       {step >= 7 && (
//         <div className="mt-6 space-y-2">
//           <div className="flex justify-between items-center">
//             <span className="text-sm font-medium">Hardening Progress</span>
//             <span className="text-xs text-muted-foreground">{Math.round(hardenProgress)}%</span>
//           </div>
//           <div className="w-full h-2 bg-muted/30 rounded-full overflow-hidden border border-border">
//             <div
//               className="h-full bg-gradient-to-r from-green-500 to-cyan-400 transition-all duration-500 rounded-full"
//               style={{ width: `${hardenProgress}%` }}
//             ></div>
//           </div>
//           <p className="text-xs text-muted-foreground">
//             {Math.floor((SECURITY_DRILLS.length * hardenProgress) / 100)} / {SECURITY_DRILLS.length} protections activated
//           </p>
//         </div>
//       )}

//       {/* Legend */}
//       <div className="mt-6 flex gap-4 text-xs text-muted-foreground">
//         <div className="flex items-center gap-2">
//           <div className="w-3 h-3 rounded bg-red-500/50 border border-red-500/70"></div>
//           <span>Vulnerable</span>
//         </div>
//         <div className="flex items-center gap-2">
//           <div className="w-3 h-3 rounded bg-green-500/50 border border-green-500/70"></div>
//           <span>Hardened</span>
//         </div>
//       </div>
//     </div>
//   );
// }



'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { useRealtimeSocket } from "@/lib/realtime-socket";

// Interface function ke bahar (Fixes your previous error)
interface SecurityDrill {
  id: string;
  title: string;
  description: string;
  attackType: string;
  vulnerable: boolean;
  hardened: boolean;
}

const SECURITY_DRILLS: SecurityDrill[] = [
  { id: '1', title: 'Rate Limiting', description: 'Request throttling attack', attackType: 'DoS', vulnerable: true, hardened: false },
  { id: '2', title: 'Auth Security', description: 'Token expiration attacks', attackType: 'Auth', vulnerable: true, hardened: false },
  { id: '3', title: 'Response Logic', description: 'Empty/Malformed response handling', attackType: 'Logic', vulnerable: true, hardened: false },
  { id: '4', title: 'Data Pagination', description: 'Pagination overflow/limit bypass', attackType: 'Data', vulnerable: true, hardened: false },
  { id: '5', title: 'Network Defense', description: 'Network timeout & latency simulation', attackType: 'Network', vulnerable: true, hardened: false },
  { id: '6', title: 'Schema Validation', description: 'Nested error & schema mismatch', attackType: 'Validation', vulnerable: true, hardened: false },
  { id: '7', title: 'Payload Integrity', description: 'Missing required field validation', attackType: 'Injection', vulnerable: true, hardened: false },
  { id: '8', title: 'Input Sanitization', description: 'General XSS & Malformed input', attackType: 'Validation', vulnerable: true, hardened: false },
];
interface SecurityDrillGridProps {
  step?: number;
}

export function SecurityDrillGrid({ step = 0 }: SecurityDrillGridProps) {
  const { messages } = useRealtimeSocket();
  const [drills, setDrills] = useState<SecurityDrill[]>(SECURITY_DRILLS);
  const [hardenProgress, setHardenProgress] = useState(0);

  // REAL-TIME INTEGRATION
  // useEffect(() => {
  //   // Backend se drill_status signals pakadne ke liye
  //   const latestDrill = messages.filter(m => m.type === 'drill_status').pop();
    
  //   if (latestDrill) {
  //     const { id, status } = latestDrill.data;
  //     setDrills(prev => prev.map(drill => {
  //       // Match by ID or Title (case-insensitive)
  //       if (drill.id === id || drill.title.toLowerCase().includes(id.toLowerCase())) {
  //         return {
  //           ...drill,
  //           vulnerable: status === 'vulnerable',
  //           hardened: status === 'safe' || status === 'hardened'
  //         };
  //       }
  //       return drill;
  //     }));
  //   }

  //   // Progress Bar Calculation (Based on actual hardened count)
  //   const hardenedCount = drills.filter(d => d.hardened).length;
  //   setHardenProgress((hardenedCount / SECURITY_DRILLS.length) * 100);

  // }, [messages, drills.length]);
  // REAL-TIME INTEGRATION (FIXED)
  useEffect(() => {
  // Backend se aane wale messages ko filter karo
  const drillMessages = messages.filter(m => m.type === 'drill_status');
    if (drillMessages.length === 0) return;

    const latestDrill = drillMessages[drillMessages.length - 1];
    if (latestDrill) {
      const { id, status } = latestDrill.data;
      setDrills(prev => {
        const updated = prev.map(drill => {
          // Backend ID '1' bhej raha hai aur frontend ID '1' hai (Exact Match)
          // Ya phir agar backend task name bhej raha hai toh title se match karoif (drill.id === String(id) || drill.title.toLowerCase().includes(String(id).toLowerCase().replace(/_/g, ' '))) {
          if (drill.id === String(id) || drill.title.toLowerCase().includes(String(id).toLowerCase().replace(/_/g, ' '))) {
            return {
              ...drill,
              vulnerable: status !== 'safe',
              hardened: status === 'safe'
            };
          }
          return drill;
        });

        // Progress calculate karne ke liye updated array ka use karo
        const hardenedCount = updated.filter(d => d.hardened).length;
        setHardenProgress((hardenedCount / SECURITY_DRILLS.length) * 100);
        
        return updated;
      });
    }
  }, [messages]); // Dependency array clean rakho
  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-bold mb-2">Security Drill Results</h3>
        <p className="text-sm text-muted-foreground mb-4">Real-time attack simulation and hardening status</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {drills.map((drill, idx) => (
          <Card
            key={drill.id}
            className={`relative overflow-hidden border transition-all duration-300 ${
              drill.hardened
                ? 'bg-green-500/10 border-green-500/30 shadow-sm hover:shadow-md'
                : drill.vulnerable
                ? 'bg-red-500/10 border-red-500/30 shadow-sm hover:shadow-md'
                : 'bg-muted/20 border-border'
            }`}
            style={{ animationDelay: `${idx * 50}ms` }}
          >
            <CardContent className="p-3">
              <div className="space-y-2">
                <div className="flex items-start justify-between">
                  <h4 className="font-medium text-sm leading-tight">{drill.title}</h4>
                  {drill.hardened ? (
                    <span className="text-lg fade-in">✓</span>
                  ) : drill.vulnerable ? (
                    <span className="text-lg status-indicator">⚠</span>
                  ) : null}
                </div>
                <p className="text-xs text-muted-foreground">{drill.description}</p>
                <div className="flex gap-1 flex-wrap mt-2">
                  <span className={`text-xs px-2 py-1 rounded-lg ${
                    drill.hardened 
                      ? 'bg-green-500/20 text-green-300'
                      : drill.vulnerable
                      ? 'bg-red-500/20 text-red-300'
                      : 'bg-muted/50 text-muted-foreground'
                  }`}>
                    {drill.attackType}
                  </span>
                </div>
              </div>

              <div className="absolute bottom-0 left-0 h-0.5 transition-all duration-300" 
                style={{
                  background: drill.hardened 
                    ? 'rgb(34, 197, 94)'
                    : drill.vulnerable
                    ? 'rgb(239, 68, 68)'
                    : 'transparent',
                  width: '100%'
                }}>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {step >= 7 && (
        <div className="mt-6 space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium">Hardening Progress</span>
            <span className="text-xs text-muted-foreground">{Math.round(hardenProgress)}%</span>
          </div>
          <div className="w-full h-2 bg-muted/30 rounded-full overflow-hidden border border-border">
            <div
              className="h-full bg-gradient-to-r from-green-500 to-cyan-400 transition-all duration-500 rounded-full"
              style={{ width: `${hardenProgress}%` }}
            ></div>
          </div>
          <p className="text-xs text-muted-foreground">
            {drills.filter(d => d.hardened).length} / {SECURITY_DRILLS.length} protections activated
          </p>
        </div>
      )}

      <div className="mt-6 flex gap-4 text-xs text-muted-foreground">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-red-500/50 border border-red-500/70"></div>
          <span>Vulnerable</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-green-500/50 border border-green-500/70"></div>
          <span>Hardened</span>
        </div>
      </div>
    </div>
  );
}