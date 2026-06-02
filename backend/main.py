from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from api.routes import router

app = FastAPI(title="NEXTRADER", version="1.0.0",
              description="Evolutionary Multi-Strategy Algo Trader — Indian Markets")

app.add_middleware(CORSMiddleware,
    allow_origins=["http://localhost:5173","http://localhost:3000"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(router)

@app.on_event("startup")
async def startup():
    await init_db()
    print("✅ NEXTRADER backend started — http://localhost:8000")
    print("📊 API docs — http://localhost:8000/docs")
