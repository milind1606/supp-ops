import os
from pathlib import Path

def make_file(path: str, content: str):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"📦 Initialised: {path}")

# =====================================================================
# SERVICE LAYER: CENTRAL ORCHESTRATOR - COORDINATOR & APPLICATION ENTRY
# =====================================================================

make_file(
    "support-ops-central-orchestrator/src/orchestrator.py",
    """
import uuid
import httpx
import os
from src.state import RedisStateRegistry
from langchain_aws import ChatBedrock

class SupportOpsCoordinator:
    def __init__(self):
        self.registry = RedisStateRegistry()
        self.llm = ChatBedrock(
            model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
            region_name=os.getenv("AWS_BEDROCK_REGION", "us-east-1")
        )
        self.discovery_url = os.getenv("PLATFORM_DISCOVERY_URL", "http://support-ops-platform-discovery:8001/discover")
        self.ansible_url = os.getenv("ANSIBLE_TRIGGER_URL", "http://support-ops-ansible-trigger:8001/execute")
        self.validator_url = os.getenv("VALIDATOR_URL", "http://support-ops-validator:8001/validate")

    async def run(self, payload: dict) -> dict:
        tx_id = str(uuid.uuid4())
        self.registry.init_transaction(tx_id, payload)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Step 1: Topology Verification & Parent Platform Routing
            self.registry.log_event(tx_id, "ORCHESTRATOR", "Routing transaction context to Platform Discovery Agent.")
            disc_res = await client.post(self.discovery_url, json={"payload": payload, "transaction_id": tx_id})
            if disc_res.status_code != 200:
                return self._abort(tx_id, f"Discovery service failure with status code: {disc_res.status_code}")
            
            disc_data = disc_res.json()
            self.registry.update_agent_output(tx_id, "platform_discovery", disc_data)
            
            analyzer_url = disc_data.get("analyzer_target_url")
            if not analyzer_url:
                return self._abort(tx_id, "Discovery agent failed to resolve a downstream sub-agent analyzer route.")

            # Step 2: Specialized Knowledge Retrieval & Analysis
            self.registry.log_event(tx_id, "ORCHESTRATOR", f"Forwarding payload to assigned platform analyzer: {analyzer_url}")
            anal_res = await client.post(analyzer_url, json={"payload": payload, "transaction_id": tx_id})
            if anal_res.status_code != 200:
                return self._abort(tx_id, f"Target platform alert analyzer failed with status code: {anal_res.status_code}")
            
            anal_data = anal_res.json()
            self.registry.update_agent_output(tx_id, "analyzer", anal_data)

            # Step 3: Automated Remediation via Ansible Playbook Dispatches
            self.registry.log_event(tx_id, "ORCHESTRATOR", "Dispatching infrastructure resolution parameters to Ansible Trigger Agent.")
            ans_res = await client.post(self.ansible_url, json={"analyzer_output": anal_data, "transaction_id": tx_id})
            if ans_res.status_code != 200:
                return self._abort(tx_id, f"Ansible orchestration workflow failed with status code: {ans_res.status_code}")
            
            ans_data = ans_res.json()
            self.registry.update_agent_output(tx_id, "ansible_trigger", ans_data)

            # Step 4: Auditor Verification Loop & Jira Comment Injection
            execution_logs = self.registry.get_complete_logs(tx_id)
            self.registry.log_event(tx_id, "ORCHESTRATOR", "Submitting holistic trace history logs to Evaluator Critic Validator.")
            
            val_res = await client.post(self.validator_url, json={
                "transaction_id": tx_id,
                "execution_logs": execution_logs,
                "payload": payload
            })
            if val_res.status_code != 200:
                return self._abort(tx_id, f"Central system validation verification error with status code: {val_res.status_code}")
            
            val_data = val_res.json()
            status = val_data.get("status", "FAILED")
            summary = val_data.get("summary", "Validation loop processed execution step mappings.")
            
            self.registry.finalize_transaction(tx_id, status, summary)
            return {
                "transaction_id": tx_id,
                "status": status,
                "summary": summary,
                "resolution_details": {"analyzer": anal_data, "ansible": ans_data, "validator": val_data}
            }

    def _abort(self, tx_id: str, error_msg: str) -> dict:
        self.registry.finalize_transaction(tx_id, "FAILED", error_msg)
        return {"transaction_id": tx_id, "status": "FAILED", "summary": error_msg, "resolution_details": {}}
"""
)

make_file(
    "support-ops-central-orchestrator/src/main.py",
    """
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from src.orchestrator import SupportOpsCoordinator

app = FastAPI(title="Support Ops Core Orchestration Hub", version="1.0.0")
coordinator = SupportOpsCoordinator()

class TicketInput(BaseModel):
    alert: str
    ticket_description: str
    additional_context: Optional[str] = None
    application_name: str

@app.post("/orchestrate")
async def orchestrate_transaction(payload: TicketInput):
    result = await coordinator.run(payload.model_dump())
    return result

@app.get("/healthz")
def health():
    return {"status": "healthy"}
"""
)

# Operational test suite configurations
make_file(
    "support-ops-central-orchestrator/tests/test_orchestrator.py",
    """
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_healthz_endpoint():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
"""
)

print("\n--- [PART 5 OF 10: CENTRAL COORDINATOR MODULE COMPLETED] ---")
