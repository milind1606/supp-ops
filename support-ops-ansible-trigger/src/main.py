from fastapi import FastAPI
from pydantic import BaseModel
from src.client import AnsibleTowerClient

app = FastAPI(title="Support Ops Ansible Orchestration Dispatcher", version="1.0.0")
client = AnsibleTowerClient()

class AnsiblePayload(BaseModel):
    analyzer_output: dict
    transaction_id: str

@app.post("/execute")
async def execute_automation_workflow(data: AnsiblePayload):
    playbook = data.analyzer_output.get("inferred_playbook", "unknown_remediation_core")
    host = data.analyzer_output.get("target_host", "UNKNOWN")
    
    result = await client.execute_playbook(playbook, host)
    return {
        "execution_status": result.get("status", "successful"),
        "job_id": result.get("job_id"),
        "playbook_dispatched": playbook,
        "target_node": host,
        "raw_log": result.get("output", "No logs returned from infrastructure context.")
    }

@app.get("/healthz")
def health():
    return {"status": "healthy"}
