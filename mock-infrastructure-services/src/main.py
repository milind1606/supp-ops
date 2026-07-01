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
        "output": f"PLAY [Remediation Task Verification] ********************\\nTASK [exec] \\nchanged: [{payload.limit_host}]"
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
