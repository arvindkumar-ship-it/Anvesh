'use client';

import React, { useState, useEffect } from 'react';
import { Badge } from '@/components/ui/badge';

const PIPELINE_STEPS = [
  { id: 1, name: 'Threat Analysis', status: 'pending' },
  { id: 2, name: 'Code Generation', status: 'pending' },
  { id: 3, name: 'Validation', status: 'pending' },
  { id: 4, name: 'Security Scan', status: 'pending' },
  { id: 5, name: 'Attack Simulation', status: 'pending' },
  { id: 6, name: 'Failure Detection', status: 'pending' },
  { id: 7, name: 'Adversarial Test', status: 'pending' },
  { id: 8, name: 'Code Hardening', status: 'pending' },
  { id: 9, name: 'Final Validation', status: 'pending' },
  { id: 10, name: 'Deployment Ready', status: 'pending' },
];

interface PipelineStep {
  id: number;
  name: string;
  status: 'pending' | 'active' | 'completed' | 'failed';
}

interface LiveStatusSidebarProps {
  currentStep?: number;
  onStepChange?: (stepId: number) => void;
  fallbackAlert?: string;
}

export function LiveStatusSidebar({ 
  currentStep = 1, 
  fallbackAlert,
}: LiveStatusSidebarProps) {
  const [steps, setSteps] = useState<PipelineStep[]>(
    PIPELINE_STEPS.map(step => ({
      ...step,
      status: step.id < currentStep ? 'completed' : step.id === currentStep ? 'active' : 'pending'
    }))
  );

  useEffect(() => {
    // Simulate step progression
    const interval = setInterval(() => {
      setSteps(prev => {
        const newSteps = [...prev];
        const activeStepIndex = newSteps.findIndex(s => s.status === 'active');
        
        if (activeStepIndex >= 0 && activeStepIndex < newSteps.length - 1) {
          newSteps[activeStepIndex].status = 'completed';
          newSteps[activeStepIndex + 1].status = 'active';
        }
        
        return newSteps;
      });
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="w-64 border-r border-border bg-card flex flex-col h-screen sticky top-0">
      {/* Header */}
      <div className="p-6 border-b border-border">
        <h2 className="text-lg font-semibold text-foreground">Pipeline</h2>
        <p className="text-xs text-muted-foreground mt-1">10 Step Audit</p>
      </div>

      {/* Steps Container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {steps.map((step, index) => (
          <div key={step.id} className="slide-in-up">
            {/* Step Item */}
            <div
              className={`px-4 py-3 rounded-xl border transition-all duration-200 ${
                step.status === 'active'
                  ? 'bg-primary/15 border-primary/40 shadow-sm'
                  : step.status === 'completed'
                  ? 'bg-green-500/10 border-green-500/25'
                  : step.status === 'failed'
                  ? 'bg-destructive/10 border-destructive/25'
                  : 'bg-muted/20 border-border'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-semibold w-6 ${
                    step.status === 'active' ? 'text-primary' : 'text-muted-foreground'
                  }`}>
                    {String(step.id).padStart(2, '0')}
                  </span>
                  <span className="text-sm text-foreground">{step.name}</span>
                </div>
                {step.status === 'active' && (
                  <div className="w-2 h-2 bg-primary rounded-full status-indicator"></div>
                )}
                {step.status === 'completed' && (
                  <span className="text-xs text-green-400">✓</span>
                )}
              </div>
            </div>

            {/* Connector Line */}
            {index < steps.length - 1 && (
              <div className="h-0.5 mx-4 my-1 bg-border/50"></div>
            )}
          </div>
        ))}
      </div>

      {/* Fallback Alert */}
      {fallbackAlert && (
        <div className="p-4 border-t border-border bg-primary/10 slide-in-up">
          <Badge className="w-full justify-center bg-primary/20 text-primary hover:bg-primary/30 border-0">
            <span className="text-xs">🔄 {fallbackAlert}</span>
          </Badge>
        </div>
      )}

      {/* Footer */}
      <div className="p-4 border-t border-border">
        <div className="text-xs text-muted-foreground space-y-2">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-primary rounded-full status-indicator"></div>
            <span>Active: {steps.find(s => s.status === 'active')?.id || '--'}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span>Done: {steps.filter(s => s.status === 'completed').length}/10</span>
          </div>
        </div>
      </div>
    </div>
  );
}
