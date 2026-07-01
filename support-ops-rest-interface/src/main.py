from fastapi import FastAPI, HTTPException
from src.models import TicketPayload, ExecutionResponse
from src.client import OrchestratorClient

app = FastAPI(title="Support Ops REST Ingress Edge", version="1.0.0")
client = OrchestratorClient()

@app.post("/api/v1/tickets", response_model=ExecutionResponse)
async def process_ticket(payload: TicketPayload):
    result = await client.forward_ticket(payload)
    return ExecutionResponse(
        transaction_id=result.get("transaction_id", "UNKNOWN-TX"),
        status=result.get("status", "FAILED"),
        summary=result.get("summary", "Internal error routing transactional footprint"),
        resolution_details=result.get("resolution_details", {})
    )

@app.get("/healthz")
def health_check():
    return {"status": "healthy"}
