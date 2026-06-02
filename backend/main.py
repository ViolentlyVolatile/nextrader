from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from api.routes import router as base_router
from api.routes.paper import router as paper_router
from api.routes.evolution import router as evolution_router
from api.websocket import manager

app = FastAPI(title="NEXTRADER", version="2.0.0",
              description="Evolutionary Multi-Strategy Algo Trader — Indian Markets")

app.add_middleware(CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(base_router)
app.include_router(paper_router)
app.include_router(evolution_router)

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()   # keep-alive
    except Exception:
        manager.disconnect(ws)

@app.on_event("startup")
async def startup():
    await init_db()
    print("✅ NEXTRADER v2.0 started")
    print("   API  → http://localhost:8000/docs")
    print("   WS   → ws://localhost:8000/ws")

@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0", "phase": "Phase 2+3 — Paper Trading + Evolution"}
