"""
Genetic Algorithm Strategy Optimizer (Phase 3).
Evolves strategy parameters over generations.
Fitness = weighted combination of Sharpe, win rate, max drawdown, profit factor.
"""
import random
import copy
import asyncio
from data import fetch_daily
from backtester import Backtester

# ── Parameter search spaces per strategy ─────────────────────────────────────

PARAM_RANGES = {
    "MomentumRSI": {
        "rsi_period": (7, 21, "int"),
        "rsi_os":     (25, 45, "int"),
        "rsi_ob":     (55, 75, "int"),
        "roc_period": (5, 20,  "int"),
    },
    "EMACrossover": {
        "fast": (5,  15, "int"),
        "slow": (15, 50, "int"),
    },
    "SupertrendADX": {
        "st_p":  (5,   14,  "int"),
        "st_m":  (1.5, 4.0, "float"),
        "adx_p": (10,  21,  "int"),
        "adx_th":(20,  35,  "int"),
    },
    "BollingerSqueeze": {
        "bb_p": (10, 30, "int"),
        "kc_p": (10, 30, "int"),
    },
    "StochasticSwing": {
        "k":  (9,  21, "int"),
        "d":  (2,   5, "int"),
        "sm": (2,   5, "int"),
        "os": (15, 30, "int"),
        "ob": (70, 85, "int"),
    },
    "MACDDivergence": {
        "fast":   (8,  16, "int"),
        "slow":   (20, 32, "int"),
        "signal": (7,  12, "int"),
        "lb":     (5,  15, "int"),
    },
    "VWAPReversion": {
        "dev_threshold": (0.01, 0.04, "float"),
    },
    "ParabolicSAR": {
        "step":  (0.01, 0.04, "float"),
        "max":   (0.15, 0.30, "float"),
        "ema_p": (30,   70,   "int"),
    },
}


def _rand_individual(ranges: dict) -> dict:
    ind = {}
    for k, (lo, hi, typ) in ranges.items():
        ind[k] = random.randint(int(lo), int(hi)) if typ == "int" \
                 else round(random.uniform(float(lo), float(hi)), 3)
    return ind


def _crossover(p1: dict, p2: dict) -> dict:
    return {k: p1[k] if random.random() < 0.5 else p2[k] for k in p1}


def _mutate(ind: dict, ranges: dict, rate: float = 0.25) -> dict:
    m = copy.deepcopy(ind)
    for k, (lo, hi, typ) in ranges.items():
        if random.random() < rate:
            m[k] = random.randint(int(lo), int(hi)) if typ == "int" \
                   else round(random.uniform(float(lo), float(hi)), 3)
    return m


def _fitness(result: dict) -> float:
    if "error" in result or result.get("total_trades", 0) < 5:
        return 0.0
    sh  = max(min(result.get("sharpe_ratio", 0), 3.0), -1.0) / 3.0
    wr  = result.get("win_rate", 0.0)
    dd  = 1 + max(result.get("max_drawdown_pct", -1.0), -0.5)   # 0=bad, 1=good
    pf  = min(result.get("profit_factor", 0), 3.0) / 3.0
    return round((sh * 0.35 + wr * 0.25 + dd * 0.25 + pf * 0.15) * 100, 2)


class GeneticOptimizer:
    def __init__(self, strategy_name: str, symbol: str = "RELIANCE",
                 days: int = 365, pop_size: int = 12, generations: int = 8):
        self.strategy_name = strategy_name
        self.symbol        = symbol
        self.days          = days
        self.pop_size      = pop_size
        self.generations   = generations
        self.history: list[dict] = []
        self._progress: dict     = {"status": "idle", "generation": 0, "best_fitness": 0}

    async def run(self) -> dict:
        ranges = PARAM_RANGES.get(self.strategy_name)
        if not ranges:
            return {"error": f"No param ranges for {self.strategy_name}"}

        df = await fetch_daily(self.symbol, "NSE", self.days)
        if df is None or len(df) < 90:
            return {"error": "Insufficient data"}

        self._progress = {"status": "running", "generation": 0, "best_fitness": 0, "total": self.generations}
        population = [_rand_individual(ranges) for _ in range(self.pop_size)]

        best_params   = population[0]
        best_fitness  = 0.0

        for gen in range(self.generations):
            # Score all individuals
            scored = []
            for ind in population:
                bt  = Backtester()
                res = bt.run(self.symbol, df, {self.strategy_name: ind})
                fit = _fitness(res)
                scored.append((ind, fit))
                await asyncio.sleep(0)  # yield to event loop

            scored.sort(key=lambda x: x[1], reverse=True)
            gen_best    = scored[0][1]
            gen_avg     = sum(s for _, s in scored) / len(scored)

            if gen_best > best_fitness:
                best_fitness = gen_best
                best_params  = scored[0][0]

            self.history.append({
                "generation":   gen,
                "best_fitness": gen_best,
                "avg_fitness":  round(gen_avg, 2),
            })
            self._progress = {
                "status":       "running",
                "generation":   gen + 1,
                "total":        self.generations,
                "best_fitness": best_fitness,
            }

            # Evolve: elitism (top 25%) + crossover + mutation
            elite_n = max(self.pop_size // 4, 2)
            new_pop = [ind for ind, _ in scored[:elite_n]]
            while len(new_pop) < self.pop_size:
                p1 = random.choice(scored[:elite_n * 2])[0]
                p2 = random.choice(scored[:elite_n * 2])[0]
                new_pop.append(_mutate(_crossover(p1, p2), ranges))
            population = new_pop

        self._progress = {"status": "complete", "generation": self.generations, "best_fitness": best_fitness, "total": self.generations}

        return {
            "strategy":     self.strategy_name,
            "symbol":       self.symbol,
            "best_params":  best_params,
            "best_fitness": best_fitness,
            "generations":  self.history,
            "status":       "complete",
        }

    def progress(self) -> dict:
        return self._progress
