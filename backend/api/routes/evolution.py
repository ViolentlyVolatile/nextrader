from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
import asyncio
from evolution import GeneticOptimizer, PARAM_RANGES, StrategyGraveyard
from strategies.all_strategies import ALL_STRATEGIES

router = APIRouter(prefix="/api/evolution", tags=["evolution"])

# In-memory stores
_opt_jobs:  dict[str, GeneticOptimizer]  = {}
_opt_results: dict[str, dict]            = {}
_graveyard: StrategyGraveyard = StrategyGraveyard([cls.name for cls in ALL_STRATEGIES])


# ── Genetic optimizer ─────────────────────────────────────────────────────────

class OptimizeRequest(BaseModel):
    strategy_name: str
    symbol:        str = "RELIANCE"
    days:          int = 365
    population:    int = 12
    generations:   int = 8


async def _run_job(key: str, opt: GeneticOptimizer):
    result = await opt.run()
    _opt_results[key] = result


@router.post("/optimize")
async def optimize(req: OptimizeRequest, bg: BackgroundTasks):
    if req.strategy_name not in PARAM_RANGES:
        return {"error": f"No param ranges defined for '{req.strategy_name}'",
                "available": list(PARAM_RANGES.keys())}
    key = f"{req.strategy_name}_{req.symbol}"
    opt = GeneticOptimizer(
        strategy_name=req.strategy_name,
        symbol=req.symbol,
        days=req.days,
        pop_size=req.population,
        generations=req.generations,
    )
    _opt_jobs[key]    = opt
    _opt_results[key] = {"status": "running", "strategy": req.strategy_name}
    bg.add_task(_run_job, key, opt)
    return {"status": "started", "key": key}


@router.get("/optimize/{key}/progress")
async def progress(key: str):
    opt = _opt_jobs.get(key)
    if not opt:
        return {"error": "Job not found"}
    return opt.progress()


@router.get("/optimize/{key}/result")
async def result(key: str):
    return _opt_results.get(key, {"status": "not_found"})


@router.get("/optimize/strategies/available")
async def available_strategies():
    return {"strategies": list(PARAM_RANGES.keys())}


# ── Strategy graveyard ────────────────────────────────────────────────────────

@router.get("/graveyard")
async def graveyard():
    return {
        "summary": _graveyard.summary(),
        "strategies": _graveyard.all_records(),
    }


@router.post("/graveyard/record")
async def record_trade(strategy_name: str, net_pnl: float, confidence: float):
    _graveyard.record(strategy_name, net_pnl, confidence)
    return {"status": "recorded"}


@router.get("/graveyard/{strategy_name}/active")
async def is_active(strategy_name: str):
    return {"strategy": strategy_name, "active": _graveyard.is_active(strategy_name)}
