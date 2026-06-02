from fastapi import APIRouter
from pydantic import BaseModel
import asyncio
from paper_trader import PaperSimulator, get_simulator, set_simulator

router = APIRouter(prefix="/api/paper", tags=["paper_trading"])


class StartRequest(BaseModel):
    symbols: list[str] | None = None


@router.post("/start")
async def start(req: StartRequest):
    sim = get_simulator()
    if sim and sim._running:
        return {"status": "already_running", "symbols": sim.symbols}
    sim = PaperSimulator(req.symbols)
    set_simulator(sim)
    asyncio.create_task(sim.start())
    return {"status": "started", "symbols": sim.symbols}


@router.post("/stop")
async def stop():
    sim = get_simulator()
    if sim:
        sim.stop()
        set_simulator(None)
    return {"status": "stopped"}


@router.get("/status")
async def status():
    sim = get_simulator()
    if not sim:
        return {"running": False}
    return {"running": sim._running, "symbols": sim.symbols}


@router.get("/portfolio")
async def portfolio():
    sim = get_simulator()
    if not sim:
        return {"error": "Paper trading not running. POST /api/paper/start first."}
    return sim.portfolio.snapshot()


@router.get("/signals")
async def signals(limit: int = 50):
    sim = get_simulator()
    if not sim:
        return {"signals": []}
    return {"signals": sim.signal_log[:limit]}


@router.get("/trades")
async def trades(limit: int = 100):
    sim = get_simulator()
    if not sim:
        return {"trades": []}
    return {"trades": sim.portfolio.recent_trades(limit)}


@router.get("/equity")
async def equity():
    sim = get_simulator()
    if not sim:
        return {"equity_curve": []}
    return {"equity_curve": sim.portfolio.equity_curve}
