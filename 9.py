import os
from pathlib import Path

def make_file(path: str, content: str):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"📦 Initialised: {path}")

# Universal container dependency structures
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
# SERVICE LAYER: SUPPORT-OPS-ANSIBLE-TRIGGER
# =====================================================================

make_file("support-ops-ansible-trigger/requirements.txt", requirements_txt)
make_file("support-ops-ansible-trigger/Dockerfile", dockerfile_content)

make_file(
    "support-ops-ansible-trigger/samconfig.toml",
    """
version = 0.1
[default.deploy.parameters]
stack_name = "support-ops-ansible-trigger"
region = "us-east-1"
confirm_changeset = true
capabilities = "CAPABILITY_IAM"
image_repositories = ["AnsibleTriggerFunction=://amazonaws.com"]
"""
)

make_file(
    "support-ops-ansible-trigger/template.yaml",
    """
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: Ansible orchestration router dispatching playbooks against target hosts.

Resources:
  AnsibleTriggerFunction:
    Type: AWS::Serverless::Function
    Properties:
      PackageType: Image
      MemorySize: 512
      Timeout: 30
      Environment:
        Variables:
          ANSIBLE_TOWER_URL: "http://mock-infrastructure-services:8001/api/v2/job_templates/launch"
    Metadata:
      Dockerfile: Dockerfile
      DockerContext: .
"""
)

make_file("support-ops-ansible-trigger/src/__init__.py", "")

make_file(
    "support-ops-ansible-trigger/src/client.py",
    """
import httpx
import os

class AnsibleTowerClient:
    def __init__(self):
        self.endpoint = os.getenv("ANSIBLE_TOWER_URL", "http://mock-infrastructure-services:8001/api/v2/job_templates/launch")

    async def execute_playbook(self, playbook_name: str, host: str) -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                payload = {
                    "playbook_name": playbook_name,
                    "limit_host": host
                }
                response = await client.post(self.endpoint, json=payload)
                if response.status_code == 200:
                    return response.json()
                return {
                    "status": "failed",
                    "error": f"Automation edge engine returned bad status code: {response.status_code}"
                }
            except Exception as e:
                return {
                    "status": "failed",
                    "error": f"Connection exception during automation dispatch: {str(e)}"
                }
"""
)

make_file(
    "support-ops-ansible-trigger/src/main.py",
    """
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
"""
)

make_file("support-ops-ansible-trigger/tests/__init__.py", "")

print("\n--- [PART 9 OF 10: SUPPORT OPS ANSIBLE TRIGGER COMPLETE] ---")
