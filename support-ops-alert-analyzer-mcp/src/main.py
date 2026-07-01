from fastapi import FastAPI
from pydantic import BaseModel
from src.engine import McpAnalyzerEngine

app = FastAPI(title="MCP Alert Analyzer Agent Suite", version="1.0.0")
engine = McpAnalyzerEngine()

class AnalyzerPayload(BaseModel):
    payload: dict
    transaction_id: str

@app.post("/analyze")
def run_analysis(data: AnalyzerPayload):
    alert = data.payload.get("alert", "")
    return engine.analyze(alert, data.transaction_id)

@app.get("/healthz")
def health():
    return {"status": "healthy"}
