import sys
import os
import asyncio
import uvicorn
import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Path fix taaki agents aur pipelines import ho sakein
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipelines.orchestrator import HermesOrchestrator

# 1. Create Server and App
# Humne type hint use kiya hai taaki VS Code ko pata chale ye kya hai
sio: socketio.AsyncServer = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
app = FastAPI()

# 2. Wrap with ASGI App
socket_app = socketio.ASGIApp(sio, app)

# ── CORS Setup ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 3. Manual Event Registration (No Decorators = No Red Lines) ──

async def handle_connect(sid, environ):
    print(f"🔥 Client Connected: {sid}")
    await sio.emit('log', {'msg': '📡 Connected to Hermes Backend', 'type': 'success'}, to=sid)

async def handle_disconnect(sid):
    print(f"🔌 Client Disconnected: {sid}")

async def handle_start(sid, data):
    url = data.get('url')
    task = data.get('task', 'Generate hardened production code')
    
    if not url:
        await sio.emit('log_entry', {'msg': '❌ Error: No URL provided', 'type': 'error'}, to=sid)
        return

    await sio.emit('log_entry', {'msg': f'🚀 Hermes initializing for: {url}', 'type': 'info'}, to=sid)

    orch = HermesOrchestrator()
    # Background task so socket doesn't hang
    asyncio.create_task(orch.run_with_ui(url, task, sio))
    # app.py ke andar run_with_ui call hone ke baad
    #await sio.emit('audit_complete', {'report': orch.results.get("report")})

# Registering events manually
sio.on('connect', handle_connect)
sio.on('disconnect', handle_disconnect)
sio.on('start_pipeline', handle_start)

# ── End of Registration ──

if __name__ == "__main__":
    # socket_app ko hi run karna hai uvicorn se
    uvicorn.run(socket_app, host="0.0.0.0", port=8000)