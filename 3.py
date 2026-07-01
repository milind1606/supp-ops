import os
from pathlib import Path

def make_file(path: str, content: str):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"📦 Initialised: {path}")

# Core multi-stage docker dependencies
requirements_txt = """
fastapi==0.111.0
uvicorn==0.30.1
pydantic==2.7.4
httpx==0.27.0
pytest==8.2.2
"""

dockerfile_content = """
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim AS runner
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY ./src ./src
ENV PATH=/root/.local/bin:$PATH
EXPOSE 8001
ENTRYPOINT ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]
"""

# =====================================================================
# SERVICE LAYER: REST INTERFACE
# =====================================================================

make_file("rest-interface/requirements.txt", requirements_txt)
make_file("rest-interface/Dockerfile", dockerfile_content)

make_file(
    "rest-interface/samconfig.toml",
    """
version = 0.1
[default.deploy.parameters]
stack_name = "support-ops-rest-interface"
region = "us-east-1"
confirm_changeset = true
capabilities = "CAPABILITY_IAM"
image_repositories = ["RestInterfaceFunction=://amazonaws.com"]
"""
)

make_file(
    "rest-interface/template.yaml",
    """
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: REST API gateway interface edge layer isolating support-ops ticket properties.

Resources:
  RestInterfaceFunction:
    Type: AWS::Serverless::Function
    Properties:
      PackageType: Image
      MemorySize: 512
      Timeout: 30
      Environment:
        Variables:
          ORCHESTRATOR_URL: "http://support-ops-central-orchestrator:8001/orchestrate"
          LANGCHAIN_TRACING_V2: "true"
          LANGCHAIN_PROJECT: "support-ops-rest-ingress"
    Metadata:
      Dockerfile: Dockerfile
      DockerContext: .
"""
)

make_file("rest-interface/src/__init__.py", "")

make_file(
    "rest-interface/src/models.py",
    """
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class TicketPayload(BaseModel):
    alert: str = Field(..., description="The telemetry tool alert name or critical criteria")
    ticket_description: str = Field(..., description="Context extracted directly from the system ticket content")
    additional_context: Optional[str] = Field(None, description="Optional cluster configuration parameters")
    application_name: str = Field(..., description="Target parent system runtime application identifier")

class ExecutionResponse(BaseModel):
    transaction_id: str
    status: str
    summary: str
    resolution_details: Dict[str, Any]
"""
)

make_file(
    "rest-interface/src/client.py",
    """
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
"""
)

make_file(
    "rest-interface/src/main.py",
    """
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
"""
)

make_file("rest-interface/tests/__init__.py", "")

make_file(
    "rest-interface/tests/test_api.py",
    """
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
"""
)

print("\n--- [PART 3 OF 10: REST INTERFACE LAYER INITIALISED] ---")
