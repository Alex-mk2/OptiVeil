from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routers import strategy, scanner, reports, intelligence, persistence, validation


app = FastAPI(
    title="OptiVeil Core API",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost",
    "http://localhost:80",
    "http://127.0.0.1",
    "http://127.0.0.1:80"], 
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)


app.include_router(strategy.router)
app.include_router(scanner.router)
app.include_router(reports.router)
app.include_router(intelligence.router)
app.include_router(persistence.router)
app.include_router(validation.router)


@app.get("/")
def health_check():
    return {"status": "OptiVeil API is running"}









