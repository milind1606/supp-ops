from fastapi import FastAPI
from pydantic import BaseModel
from src.engine import TopologyDiscoveryEngine

app = FastAPI(title="Support Ops Discovery Layer", version="1.0.0")
engine = TopologyDiscoveryEngine()

class DiscoveryPayload(BaseModel):
    payload: dict
    transaction_id: str

@app.post("/discover")
def discover_platform(data: DiscoveryPayload):
    alert = data.payload.get("alert", "")
    description = data.payload.get("ticket_description", "")
    return engine.discover_target(alert, description)

@app.get("/healthz")
def health():
    return {"status": "healthy"}
