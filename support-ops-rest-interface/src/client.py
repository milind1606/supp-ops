import httpx
import os
from src.models import TicketPayload

class OrchestratorClient:
    def __init__(self):
        self.orchestrator_url = os.getenv("ORCHESTRATOR_URL", "http://support-ops-central-orchestrator:8001/orchestrate")

    async def forward_ticket(self, payload: TicketPayload) -> dict:
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(self.orchestrator_url, json=payload.model_dump())
                if response.status_code == 200:
                    return response.json()
                return {
                    "transaction_id": "UNKNOWN-TX",
                    "status": "FAILED",
                    "summary": f"Orchestrator pipeline error status code: {response.status_code}",
                    "resolution_details": {"error_body": response.text}
                }
            except Exception as e:
                return {
                    "transaction_id": "UNKNOWN-TX",
                    "status": "FAILED",
                    "summary": f"Ingress connection exception failed: {str(e)}",
                    "resolution_details": {}
                }
