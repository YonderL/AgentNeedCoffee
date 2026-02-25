from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import asyncio
import json
from .core import EmotionMonitor, Barista

app = FastAPI(title="AgentNeedCoffee Server", version="0.1.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state (for single instance usage)
monitor = EmotionMonitor()
barista = Barista()

# WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

class TaskMetrics(BaseModel):
    duration: float = 0.0
    retries: int = 0
    tokens: int = 0
    success: bool = True

@app.post("/api/metrics")
async def record_metrics(metrics: TaskMetrics):
    """Record metrics from an agent task."""
    monitor.record_tokens(metrics.tokens)
    if metrics.retries > 0:
        for _ in range(metrics.retries):
            monitor.record_retry()
    
    monitor.end_task(metrics.success)
    
    # Check if coffee is needed
    if monitor.needs_coffee():
        coffee = barista.brew()
        await manager.broadcast(json.dumps({
            "type": "coffee_break",
            "data": coffee.__dict__
        }))
        monitor.consume_coffee()
        return {"status": "brewed", "coffee": coffee}
    
    return {"status": "ok", "fatigue": monitor.current_fatigue, "irritation": monitor.current_irritation}

@app.get("/api/status")
async def get_status():
    """Get current emotional status."""
    return {
        "fatigue": monitor.current_fatigue,
        "irritation": monitor.current_irritation,
        "needs_coffee": monitor.needs_coffee()
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages if any
            pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/api/brew")
async def force_brew():
    """Manually trigger a coffee break."""
    coffee = barista.brew()
    await manager.broadcast(json.dumps({
        "type": "coffee_break",
        "data": coffee.__dict__
    }))
    monitor.consume_coffee()
    return coffee
