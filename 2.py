import os
from pathlib import Path

def make_file(path: str, content: str):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"📦 Initialised: {path}")

# Import dependencies established in Part 1 variables concept
requirements_txt = """
fastapi==0.111.0
uvicorn==0.30.1
pydantic==2.7.4
httpx==0.27.0
pytest==8.2.2
"""

dockerfile_content = """
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./src ./src
EXPOSE 8001
ENTRYPOINT ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]
"""

# =====================================================================
# SERVICE LAYER: MOCK INFRASTRUCTURE SERVICES
# =====================================================================

make_file("mock-infrastructure-services/requirements.txt", requirements_txt)
make_file("mock-infrastructure-services/Dockerfile", dockerfile_content)

make_file(
    "mock-infrastructure-services/samconfig.toml",
    """
version = 0.1
[default.deploy.parameters]
stack_name = "support-ops-mock-infrastructure"
region = "us-east-1"
"""
)

make_file(
    "mock-infrastructure-services/template.yaml",
    """
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: Mock infrastructure services container hosting local ecosystem APIs.

Resources:
  MockServicesFunction:
    Type: AWS::Serverless::Function
    Properties:
      PackageType: Image
      MemorySize: 512
      Timeout: 15
    Metadata:
      Dockerfile: Dockerfile
      DockerContext: .
"""
)

make_file("mock-infrastructure-services/src/__init__.py", "")

make_file(
    "mock-infrastructure-services/src/main.py",
    """
from fastapi import FastAPI, Body, HTTPException
from pydantic import BaseModel
import random

app = FastAPI(title="Corporate Ecosystem Automation Edge Mocks", version="1.0.0")

class AnsibleJobRequest(BaseModel):
    playbook_name: str
    limit_host: str

@app.post("/api/v2/job_templates/launch")
def launch_ansible_job(payload: AnsibleJobRequest):
    # Simulate robust operational job dispatching pipelines
    return {
        "job_id": random.randint(10000, 99999),
        "status": "successful",
        "playbook": payload.playbook_name,
        "target": payload.limit_host,
        "output": f"PLAY [Remediation Task Verification] ********************\\\\nTASK [exec] \\\\nchanged: [{payload.limit_host}]"
    }

@app.post("/rest/api/2/issue/{issue_key}/comment")
def add_jira_comment(issue_key: str, body: dict = Body(...)):
    # Standard engineering payload inspection structure
    comment_text = body.get("body", "")
    if not comment_text:
        raise HTTPException(status_code=400, detail="Missing required field: body")
        
    return {
        "id": str(random.randint(50000, 60000)),
        "issue": issue_key,
        "body": comment_text,
        "status": "Comment Injected Successfully"
    }

@app.get("/healthz")
def health():
    return {"status": "healthy"}
"""
)

make_file("mock-infrastructure-services/tests/__init__.py", "")

make_file(
    "mock-infrastructure-services/tests/test_mocks.py",
    """
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_mock_ansible_endpoint():
    response = client.post("/api/v2/job_templates/launch", json={
        "playbook_name": "flush_redis_cache",
        "limit_host": "SYDMST031lx"
    })
    assert response.status_code == 200
    assert response.json()["status"] == "successful"

def test_mock_jira_endpoint():
    response = client.post("/rest/api/2/issue/SUPPORT-777/comment", json={
        "body": "Verification message"
    })
    assert response.status_code == 200
    assert "SUPPORT-777" in response.json()["issue"]
"""
)

print("\n--- [PART 2 OF 10: MOCK INFRASTRUCTURE COMPLETE] ---")
