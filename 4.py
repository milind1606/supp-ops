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
langgraph==0.1.4
redis==5.0.7
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
# SERVICE LAYER: CENTRAL ORCHESTRATOR - BASE CONFIG & STATE MANAGEMENT
# =====================================================================

make_file("support-ops-central-orchestrator/requirements.txt", requirements_txt)
make_file("support-ops-central-orchestrator/Dockerfile", dockerfile_content)

make_file(
    "support-ops-central-orchestrator/samconfig.toml",
    """
version = 0.1
[default.deploy.parameters]
stack_name = "support-ops-central-orchestrator"
region = "us-east-1"
confirm_changeset = true
capabilities = "CAPABILITY_IAM"
image_repositories = ["OrchestratorFunction=://amazonaws.com"]
"""
)

make_file(
    "support-ops-central-orchestrator/template.yaml",
    """
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: support-ops-central-orchestrator managing active agent streams via Amazon ElastiCache Redis.

Resources:
  ElastiCacheCluster:
    Type: AWS::ElastiCache::CacheCluster
    Properties:
      Engine: redis
      CacheNodeType: cache.t3.medium
      NumCacheNodes: 1
      VpcSecurityGroupIds:
        - !Ref RedisSecurityGroup
      EngineVersion: "7.0"

  RedisSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Inbound ElastiCache access controls for local multi-agents
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 6379
          ToPort: 6379
          CidrIp: 0.0.0.0/0

  OrchestratorFunction:
    Type: AWS::Serverless::Function
    Properties:
      PackageType: Image
      MemorySize: 1024
      Timeout: 90
      Environment:
        Variables:
          REDIS_HOST: !GetAtt ElastiCacheCluster.RedisEndpoint.Address
          REDIS_PORT: 6379
          PLATFORM_DISCOVERY_URL: "http://support-ops-platform-discovery:8001/discover"
          ANSIBLE_TRIGGER_URL: "http://support-ops-ansible-trigger:8001/execute"
          VALIDATOR_URL: "http://support-ops-validator:8001/validate"
          AWS_BEDROCK_REGION: "us-east-1"
          LANGCHAIN_TRACING_V2: "true"
          LANGCHAIN_ENDPOINT: "https://langchain.com"
          LANGCHAIN_API_KEY: "mock_key"
          LANGCHAIN_PROJECT: "support-ops-orchestration"
    Metadata:
      Dockerfile: Dockerfile
      DockerContext: .
"""
)

make_file("support-ops-central-orchestrator/src/__init__.py", "")

make_file(
    "support-ops-central-orchestrator/src/state.py",
    """
import json
import redis
import os
from typing import Dict, Any, Optional

class RedisStateRegistry:
    def __init__(self):
        # Fallback parameters matching local docker-compose environment layout parameters
        host = os.getenv("REDIS_HOST", "localhost")
        port = int(os.getenv("REDIS_PORT", 6379))
        self.client = redis.Redis(host=host, port=port, decode_responses=True)

    def init_transaction(self, transaction_id: str, initial_data: Dict[str, Any]):
        self.client.hset(f"tx:{transaction_id}", "input", json.dumps(initial_data))
        self.client.hset(f"tx:{transaction_id}", "status", "PROCESSING")
        self.log_event(transaction_id, "ORCHESTRATOR", f"Initialized distributed multi-agent support transaction: {transaction_id}")

    def log_event(self, transaction_id: str, agent_name: str, message: str, metadata: Optional[Dict[str, Any]] = None):
        log_entry = {
            "agent": agent_name,
            "message": message,
            "metadata": metadata or {}
        }
        # Emits transactional footprints down to execution stream queues for evaluation loops
        self.client.rpush(f"logs:{transaction_id}", json.dumps(log_entry))

    def update_agent_output(self, transaction_id: str, agent_name: str, output: Dict[str, Any]):
        self.client.hset(f"tx:{transaction_id}", f"output:{agent_name}", json.dumps(output))
        self.log_event(transaction_id, agent_name, f"Execution block complete. Persisted operational states.", output)

    def get_complete_logs(self, transaction_id: str) -> list:
        raw_logs = self.client.lrange(f"logs:{transaction_id}", 0, -1)
        return [json.loads(log) for log in raw_logs]

    def finalize_transaction(self, transaction_id: str, status: str, summary: str):
        self.client.hset(f"tx:{transaction_id}", "status", status)
        self.client.hset(f"tx:{transaction_id}", "summary", summary)
"""
)

print("\n--- [PART 4 OF 10: REDIS STATE REGISTRY DEPLOYED SUCCESSFULLY] ---")
