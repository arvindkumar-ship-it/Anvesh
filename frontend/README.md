# Agentic AI Security Audit Dashboard

A modern, real-time dashboard for monitoring AI agent security hardening and resilience testing.

## Features

### 1. Live Status Sidebar
- **10-Step Pipeline**: Visual representation of the AI audit process
- **Pulsing Active State**: Cyan neon effect on the currently active step
- **Fallback Alerts**: Badge notifications when switching between AI models (e.g., Gemini → Groq)
- **Progress Tracking**: Real-time completion counter

### 2. Terminal Log Viewer
- **Real-time Streaming**: Live log entries with timestamps
- **Color-coded Output**: Different colors for info, success, warnings, and errors
- **Auto-scroll**: Automatic scrolling to latest logs with manual override
- **Log History**: Maintains last 50 logs for context

### 3. Security Drill Grid
- **8 Attack Scenarios**: Organized in a 2×4 grid
- **Vulnerable → Hardened Transitions**: Cards transition from red (vulnerable) to green (hardened)
- **Visual Feedback**: Pulsing warnings and success indicators
- **Progress Bar**: Shows hardening percentage as Step 8 progresses

### 4. Code Diff Viewer
- **Side-by-Side Comparison**: Generated code vs. hardened code
- **Change Highlighting**: Green highlights for security improvements
- **Detailed Annotations**: Each change is documented with its security benefit
- **Statistics**: Shows lines added, improvements made

## Design System

### Color Palette
- **Background**: `oklch(0.08 0 0)` - Deep dark (#0D0D0D)
- **Primary (Neon Cyan)**: `oklch(0.65 0.22 262.42)` - Vibrant purple/blue
- **Success (Neon Green)**: `oklch(0.65 0.18 142.35)` - Bright green
- **Danger (Neon Red)**: `oklch(0.55 0.22 24.23)` - Bold red
- **Text**: `oklch(0.98 0 0)` - Near white (#FAF8F6)

### Animations
- **pulse-neon**: 2s pulsing glow effect for active steps
- **pulse-glow**: 2s opacity pulse for warnings
- **slide-in-up**: 0.6s entrance animation
- **glow-pulse**: 3s continuous glow effect
- **code-highlight**: 3s highlight flash for newly hardened code

## Project Structure

```
/components
  ├── live-status-sidebar.tsx      # 10-step pipeline with active state
  ├── terminal-log-viewer.tsx       # Real-time log streaming
  ├── security-drill-grid.tsx       # 2×4 attack scenario grid
  └── code-diff-viewer.tsx          # Side-by-side code comparison

/lib
  ├── realtime-socket.ts            # Socket.io integration hooks
  └── socket-setup.md               # Backend setup guide

/app
  ├── page.tsx                      # Main dashboard
  ├── layout.tsx                    # Root layout with dark theme
  └── globals.css                   # Design tokens & animations
```

## Customization

### Changing Theme Colors

Edit `/app/globals.css`:

```css
:root {
  --primary: oklch(0.65 0.22 262.42);      /* Change neon color */
  --neon-cyan: oklch(0.72 0.19 159.63);
  --neon-red: oklch(0.55 0.22 24.23);
  --neon-green: oklch(0.65 0.18 142.35);
}
```

### Adding More Steps

Edit `/components/live-status-sidebar.tsx`:

```typescript
const PIPELINE_STEPS = [
  { id: 1, name: 'Step 1', status: 'pending' },
  { id: 2, name: 'Step 2', status: 'pending' },
  // Add more steps...
];
```

### Customizing Attack Drills

Edit `/components/security-drill-grid.tsx`:

```typescript
const SECURITY_DRILLS: SecurityDrill[] = [
  { 
    id: '1', 
    title: 'Your Attack Name', 
    description: 'Description',
    attackType: 'Category',
    vulnerable: true,
    hardened: false 
  },
  // Add more drills...
];
```

## Real-time Integration

The dashboard includes Socket.io integration for real-time updates. See `/lib/socket-setup.md` for:

1. **Backend Setup**: Node.js + Express + Socket.io configuration
2. **Environment Variables**: Required `.env.local` settings
3. **Event Handling**: Step updates, log streaming, drill status changes
4. **Alternative Approaches**: SSE, polling, or third-party services

### Quick Backend Example

```javascript
io.on('connection', (socket) => {
  // Emit step updates
  io.emit('step_update', { step: currentStep });
  
  // Send logs in real-time
  io.emit('log_entry', { 
    timestamp: new Date().toLocaleTimeString(),
    type: 'info',
    message: 'Audit step 2 in progress...'
  });
});
```

## Browser Compatibility

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Requires JavaScript enabled for animations and interactivity

## Performance Tips

1. **Log Limiting**: Terminal viewer keeps only last 50 logs to prevent memory bloat
2. **Animation Throttling**: Reduce animation frequency on lower-end devices
3. **Lazy Loading**: Cards animate in with staggered delays for smooth performance
4. **Backdrop Blur**: Use `backdrop-blur-sm` for modern browsers; falls back to solid colors

## Deployment

1. **Vercel**: Run `vercel deploy` from project root
2. **Docker**: Include Node.js runtime for Socket.io backend
3. **Environment Variables**: Set `NEXT_PUBLIC_SOCKET_URL` for production

## Troubleshooting

### Animations Not Working
- Check browser support for CSS `@keyframes` and `animation`
- Ensure `@import 'tw-animate-css'` is present in globals.css

### Socket.io Connection Fails
- Verify backend is running on correct port
- Check CORS settings in backend configuration
- Ensure environment variable `NEXT_PUBLIC_SOCKET_URL` is set

### Terminal Logs Not Updating
- Check browser console for errors
- Verify log streaming events are being emitted from backend
- Ensure Socket.io connection is established (`isConnected` should be true)

## Future Enhancements

- Dark/Light theme toggle
- Export audit results as PDF
- Replay audit history
- Custom attack scenario builder
- Performance metrics dashboard
- Comparative analysis of different hardening approaches

## License

MIT - Feel free to use this dashboard for your projects!
