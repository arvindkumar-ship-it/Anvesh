'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

const DRAFT_CODE = `// Generated Code - Draft
function validateInput(input) {
  if (input === null) {
    return false;
  }
  return true;
}

function processData(data) {
  const result = eval(data);
  return result;
}

function authenticate(user) {
  if (user.role === 'admin') {
    grantAccess();
  }
}

export { validateInput, processData, authenticate };`;

const HARDENED_CODE = `// Final Code - Security Hardened
import { sanitize } from 'xss-filters';
import { rateLimit } from './middleware/rate-limit';
import { hash } from 'bcrypt';

function validateInput(input) {
  // Added null check and type validation
  if (input === null || typeof input !== 'string') {
    throw new Error('Invalid input');
  }
  if (input.length > 1000) {
    throw new Error('Input exceeds max length');
  }
  return sanitize(input);
}

function processData(data) {
  // Removed dangerous eval, use safe parser
  const sanitized = sanitize(data);
  try {
    const parser = new JSONParser();
    const result = parser.parse(sanitized);
    return result;
  } catch (e) {
    logger.error('Parse error:', e);
    return null;
  }
}

function authenticate(user) {
  // Added privilege escalation prevention
  const hashedRole = hash(user.role, 10);
  const permittedRoles = ['admin', 'user'];
  
  if (!permittedRoles.includes(user.role)) {
    logger.warn('Unauthorized role attempt:', user.role);
    throw new Error('Access denied');
  }
  
  if (user.role === 'admin' && verifyAdminToken(user.token)) {
    grantAccess();
  }
}

export { validateInput, processData, authenticate };`;

const HIGHLIGHTED_CHANGES = [
  { line: 1, change: 'Added security imports' },
  { line: 2, change: 'Added rate limiting' },
  { line: 3, change: 'Added bcrypt hashing' },
  { line: 8, change: 'Added type checking and length validation' },
  { line: 11, change: 'Added input sanitization' },
  { line: 16, change: 'Removed dangerous eval()' },
  { line: 17, change: 'Implemented safe JSON parser' },
  { line: 27, change: 'Added role hashing' },
  { line: 28, change: 'Added privilege escalation prevention' },
  { line: 29, change: 'Added role validation' },
  { line: 31, change: 'Added token verification' },
];

interface CodeDiffViewerProps {
  showDiff?: boolean;
}

export function CodeDiffViewer({ showDiff = true }: CodeDiffViewerProps) {
  const [selectedLine, setSelectedLine] = useState<number | null>(null);

  const renderCode = (code: string, isHardened: boolean) => {
    const lines = code.split('\n');
    return (
      <div className="space-y-0">
        {lines.map((line, idx) => {
          const lineNum = idx + 1;
          const change = HIGHLIGHTED_CHANGES.find(c => c.line === lineNum);
          
          return (
            <div
              key={idx}
              className={`hover:bg-muted/20 transition-colors cursor-pointer px-3 py-1 ${
                change && isHardened ? 'bg-green-500/10 border-l-2 border-green-500/50' : ''
              }`}
              onClick={() => setSelectedLine(change ? lineNum : null)}
            >
              <div className="flex gap-3">
                <span className="text-muted-foreground select-none w-8 text-right text-xs">
                  {String(lineNum).padStart(2, ' ')}
                </span>
                <code className="text-xs font-mono flex-1 text-foreground/90">
                  {line || ' '}
                </code>
              </div>
              {change && isHardened && (
                <div className="ml-11 text-xs text-green-400 py-1 pl-2 border-l border-green-500/30">
                  → {change.change}
                </div>
              )}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <Card className="bg-card/50 backdrop-blur-sm border-border col-span-full">
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Code Diff Viewer</CardTitle>
        <p className="text-xs text-muted-foreground mt-1">Before and after security hardening comparison</p>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          {/* Left: Draft Code */}
          <div className="space-y-2">
            <h4 className="text-sm font-semibold text-red-400">Generated Code (Vulnerable)</h4>
            <div className="bg-black/40 border border-red-500/30 rounded-lg overflow-hidden font-mono text-xs">
              {renderCode(DRAFT_CODE, false)}
            </div>
          </div>

          {/* Right: Hardened Code */}
          <div className="space-y-2">
            <h4 className="text-sm font-semibold text-green-400">Hardened Code (Secure)</h4>
            <div className="bg-black/40 border border-green-500/30 rounded-lg overflow-hidden font-mono text-xs">
              {renderCode(HARDENED_CODE, true)}
            </div>
          </div>
        </div>

        {/* Changes Legend */}
        <div className="mt-6 p-4 bg-muted/20 border border-border rounded-lg">
          <h4 className="text-sm font-semibold mb-3">Security Improvements Applied</h4>
          <div className="grid grid-cols-2 gap-3 text-xs">
            {HIGHLIGHTED_CHANGES.map((change, idx) => (
              <div key={idx} className="flex gap-2">
                <span className="text-green-400 font-bold">+</span>
                <span className="text-muted-foreground">{change.change}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Stats */}
        <div className="mt-4 flex gap-6 text-xs text-muted-foreground">
          <div>
            <span className="font-semibold">Draft Lines:</span> {DRAFT_CODE.split('\n').length}
          </div>
          <div>
            <span className="font-semibold">Hardened Lines:</span> {HARDENED_CODE.split('\n').length}
          </div>
          <div>
            <span className="font-semibold">Improvements:</span> {HIGHLIGHTED_CHANGES.length}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
