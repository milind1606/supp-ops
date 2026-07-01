import os
from pathlib import Path

def make_file(path: str, content: str):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"📦 Initialised: {path}")

# Configuration layout pins matching Part 1
requirements_txt = """
fastapi==0.111.0
uvicorn==0.30.1
pydantic==2.7.4
langchain==0.2.5
langchain-core==0.2.9
langchain-aws==0.1.11
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
# SERVICE LAYER: SUPPORT-OPS-VALIDATOR
# =====================================================================

make_file("support-ops-validator/requirements.txt", requirements_txt)
make_file("support-ops-validator/Dockerfile", dockerfile_content)

make_file(
    "support-ops-validator/samconfig.toml",
    """
version = 0.1
[default.deploy.parameters]
stack_name = "support-ops-validator"
region = "us-east-1"
confirm_changeset = true
capabilities = "CAPABILITY_IAM"
image_repositories = ["ValidatorFunction=://amazonaws.com"]
"""
)

make_file(
    "support-ops-validator/template.yaml",
    """
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: Centralized Evaluator Critic validation pipeline pushing analysis logs to Jira.

Resources:
  ValidatorFunction:
    Type: AWS::Serverless::Function
    Properties:
      PackageType: Image
      MemorySize: 1024
      Timeout: 60
      Environment:
        Variables:
          JIRA_COMMENT_URL_TEMPLATE: "http://mock-infrastructure-services:8001/rest/api/2/issue/{issue_key}/comment"
          AWS_BEDROCK_REGION: "us-east-1"
    Metadata:
      Dockerfile: Dockerfile
      DockerContext: .
"""
)

make_file("support-ops-validator/src/__init__.py", "")

make_file(
    "support-ops-validator/src/evaluator.py",
    """
import os
import httpx
from langchain_aws import ChatBedrock

class EvaluatorCriticEngine:
    def __init__(self):
        self.llm = ChatBedrock(
            model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
            region_name=os.getenv("AWS_BEDROCK_REGION", "us-east-1")
        )
        self.jira_template = os.getenv("JIRA_COMMENT_URL_TEMPLATE", "http://mock-infrastructure-services:8001/rest/api/2/issue/{issue_key}/comment")

    async def validate_and_comment(self, tx_id: str, logs: list, payload: dict) -> dict:
        # Reconstruct the holistic multi-agent transaction execution trace footprint
        log_str = "\\n".join([f"[{item.get('agent')}]: {item.get('message')}" for item in logs])
        
        system_prompt = (
            "You are a Senior Infrastructure Quality Auditor Validation Agent.\\n"
            "Review the multi-agent logs execution trace against system infrastructure runbooks.\\n"
            "Determine if the transaction has been successfully completed or failed.\\n"
            "Output your absolute verdict starting precisely with [STATUS]: SUCCESS or [STATUS]: FAILED.\\n"
            "Follow up with a clear summary section titled [SUMMARY]."
        )
        
        user_message = f"Transaction ID: {tx_id}\\nInput context parameters: {payload}\\n\\nExecution Logs Trace:\\n{log_str}"
        
        response = self.llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ])
        
        analysis = response.content
        status = "SUCCESS" if "[STATUS]: SUCCESS" in analysis else "FAILED"
        
        summary_text = "Automated multi-agent remediation workflow executed."
        if "[SUMMARY]" in analysis:
            summary_text = analysis.split("[SUMMARY]")[-1].strip()

        # Update Jira issue tracking system with the final comment entry
        issue_key = payload.get("application_name", "SUPPORT-KEY-101")
        await self._post_jira_comment(issue_key, tx_id, status, summary_text)

        return {"status": status, "summary": summary_text}

    async def _post_jira_comment(self, issue_key: str, tx_id: str, status: str, summary: str):
        url = self.jira_template.format(issue_key=issue_key)
        jira_body = {
            "body": f"[Multi-Agent System Central Audit Trail]\\nTransaction: {tx_id}\\nStatus: {status}\\nResolution Summary: {summary}"
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                await client.post(url, json=jira_body)
            except Exception:
                pass # Safeguard execution path from downstream tracking network issues
"""
)

make_file(
    "support-ops-validator/src/main.py",
    """
from fastapi import FastAPI
from pydantic import BaseModel
from src.evaluator import EvaluatorCriticEngine

app = FastAPI(title="Support Ops Audit Validator Interface", version="1.0.0")
engine = EvaluatorCriticEngine()

class ValidatorPayload(BaseModel):
    transaction_id: str
    execution_logs: list
    payload: dict

@app.post("/validate")
async def run_validation(data: ValidatorPayload):
    return await engine.validate_and_comment(data.transaction_id, data.execution_logs, data.payload)

@app.get("/healthz")
def health():
    return {"status": "healthy"}
"""
)

# =====================================================================
# GLOBAL WORKSPACE CONTROL INFRASTRUCTURE (README)
# =====================================================================

make_file(
    "README.md",
    """
# Support-Ops Distributed Multi-Agent Architecture

Production-grade support operations system deploying autonomous agents via **LangChain**, **LangGraph**, and **LlamaIndex** across an **AWS EKS + Fargate** cluster with an **Amazon ElastiCache for Redis** shared state registry.

## Multi-Stage Deployment & Execution Runbook

### 1. Build Layered Containers
Compile the application containers locally or via your CI/CD pipeline:
```bash
docker build -t support-ops-rest-interface:latest ./rest-interface
docker build -t support-ops-central-orchestrator:latest ./support-ops-central-orchestrator
docker build -t support-ops-platform-discovery:latest ./support-ops-platform-discovery
docker build -t support-ops-alert-analyzer-mcp:latest ./support-ops-alert-analyzer-mcp
docker build -t support-ops-alert-analyzer-mst:latest ./support-ops-alert-analyzer-mst
docker build -t support-ops-ansible-trigger:latest ./support-ops-ansible-trigger
docker build -t support-ops-validator:latest ./support-ops-validator
docker build -t mock-infrastructure-services:latest ./mock-infrastructure-services
```

### 2. Push context assets to AWS ECR
Tag your built images and push them directly to your corporate Elastic Container Registry target:
```bash
aws ecr create-repository --repository-name support-ops/central-orchestrator
docker tag support-ops-central-orchestrator:latest <ACCOUNT_ID>://
docker push <ACCOUNT_ID>://
```

### 3. Kubernetes EKS Fargate Deployment Spec
Deploy the multi-agent application pods ensuring the containers mount the required LangSmith telemetry environment variable structures:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: support-ops-central-orchestrator
  namespace: support-ops
spec:
  replicas: 2
  template:
    metadata:
      labels:
        app: central-orchestrator
    spec:
      containers:
      - name: orchestrator
        image: <ACCOUNT_ID>://
        ports:
        - containerPort: 8001
        env:
        - name: REDIS_HOST
          value: "://amazonaws.com"
        - name: LANGCHAIN_TRACING_V2
          value: "true"
        - name: LANGCHAIN_ENDPOINT
          value: "https://langchain.com"
        - name: LANGCHAIN_API_KEY
          value: "ls__your_langsmith_token"
        - name: LANGCHAIN_PROJECT
          value: "Support-Ops-Production-Fabric"
```

---

## Troubleshooting with LangSmith Telemetry

To trace multi-agent performance and run system diagnostics:
1. **Track Graph Ingress Loops**: Verify multi-service connection traces inside the LangSmith execution dashboard view.
2. **Audit LLM Context Submissions**: Open the specific `ChatBedrock` execution nodes to inspect historical context data injection sizes and prompt token counts.
3. **Analyze Latency Bottlenecks**: Identify slower API calls by reviewing step-by-step latency inside the `SupportOpsCoordinator` graph trace layout.
"""
)

print("\n--- [PART 10 OF 10: COMPLETE DISTRIBUTED APPLICATION STRUCTURE GENERATED] ---")
