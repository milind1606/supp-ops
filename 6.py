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
# SERVICE LAYER: SUPPORT-OPS-PLATFORM-DISCOVERY
# =====================================================================

make_file("support-ops-platform-discovery/requirements.txt", requirements_txt)
make_file("support-ops-platform-discovery/Dockerfile", dockerfile_content)

make_file(
    "support-ops-platform-discovery/samconfig.toml",
    """
version = 0.1
[default.deploy.parameters]
stack_name = "support-ops-platform-discovery"
region = "us-east-1"
confirm_changeset = true
capabilities = "CAPABILITY_IAM"
image_repositories = ["DiscoveryFunction=://amazonaws.com"]
"""
)

make_file(
    "support-ops-platform-discovery/template.yaml",
    """
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: System mapping engine routing topology alerts to specific analyzer nodes.

Resources:
  DiscoveryFunction:
    Type: AWS::Serverless::Function
    Properties:
      PackageType: Image
      MemorySize: 512
      Timeout: 30
      Environment:
        Variables:
          TOPOLOGY_FILE_PATH: "topoloy-all-systems/topoloy-all-systems.txt"
          MCP_ANALYZER_URL: "http://support-ops-alert-analyzer-mcp:8001/analyze"
          MST_ANALYZER_URL: "http://support-ops-alert-analyzer-mst:8001/analyze"
    Metadata:
      Dockerfile: Dockerfile
      DockerContext: .
"""
)

make_file("support-ops-platform-discovery/src/__init__.py", "")

make_file(
    "support-ops-platform-discovery/src/engine.py",
    """
import os
import re

class TopologyDiscoveryEngine:
    def __init__(self):
        self.file_path = os.getenv("TOPOLOGY_FILE_PATH", "topoloy-all-systems/topoloy-all-systems.txt")
        self.mcp_url = os.getenv("MCP_ANALYZER_URL", "http://support-ops-alert-analyzer-mcp:8001/analyze")
        self.mst_url = os.getenv("MST_ANALYZER_URL", "http://support-ops-alert-analyzer-mst:8001/analyze")

    def discover_target(self, alert_text: str, description_text: str) -> dict:
        combined = f"{alert_text} {description_text}".lower()
        
        # Absolute structural path fallback validation
        if not os.path.exists(self.file_path):
            # Check relative traversal if directory path varies during tests
            alt_path = os.path.join("..", self.file_path)
            if os.path.exists(alt_path):
                self.file_path = alt_path
            else:
                return self._apply_heuristic_fallback(combined, f"Topology map file not found at {self.file_path}")

        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()

        entries = content.split("=== ENTRY ===")
        for entry in entries:
            if not entry.strip():
                continue
            
            host_match = re.search(r"HOSTNAME:([^\\|\\n]+)", entry, re.IGNORECASE)
            env_match = re.search(r"ENVIRONMENT:([^\\|\\n]+)", entry, re.IGNORECASE)
            platform_match = re.search(r"PARENT-PLATFORM:([^\\|\\n\\s]+)", entry, re.IGNORECASE)

            if host_match and env_match and platform_match:
                host = host_match.group(1).strip().lower()
                env = env_match.group(1).strip()
                platform = platform_match.group(1).strip().upper()

                if host in combined:
                    target_url = self.mcp_url if platform == "MCP" else self.mst_url
                    return {
                        "parent_platform": platform,
                        "environment": env,
                        "hostname": host_match.group(1).strip(),
                        "analyzer_target_url": target_url
                    }

        return self._apply_heuristic_fallback(combined, "No explicit physical hostname matched topology map strings.")

    def _apply_heuristic_fallback(self, combined_text: str, reasoning: str) -> dict:
        if "mcp" in combined_text:
            return {"parent_platform": "MCP", "environment": "UNKNOWN", "hostname": "UNKNOWN", "analyzer_target_url": self.mcp_url, "notes": reasoning}
        if "mst" in combined_text:
            return {"parent_platform": "MST", "environment": "UNKNOWN", "hostname": "UNKNOWN", "analyzer_target_url": self.mst_url, "notes": reasoning}
        
        # Standard structural fallback target interface
        return {"parent_platform": "MCP", "environment": "UNKNOWN", "hostname": "UNKNOWN", "analyzer_target_url": self.mcp_url, "notes": reasoning}
"""
)

make_file(
    "support-ops-platform-discovery/src/main.py",
    """
from fastapi import FastAPI
from pydantic import BaseModel
from src.engine import TopologyDiscoveryEngine

app = FastAPI(title="Support Ops Discovery Layer", version="1.0.0")
engine = TopologyDiscoveryEngine()

class DiscoveryPayload(BaseModel):
    payload: dict
    transaction_id: str

@app.post("/discover")
def discover_platform(data: DiscoveryPayload):
    alert = data.payload.get("alert", "")
    description = data.payload.get("ticket_description", "")
    return engine.discover_target(alert, description)

@app.get("/healthz")
def health():
    return {"status": "healthy"}
"""
)

make_file("support-ops-platform-discovery/tests/__init__.py", "")

make_file(
    "support-ops-platform-discovery/tests/test_discovery.py",
    """
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_heuristic_classification_fallback():
    response = client.post("/discover", json={
        "payload": {"alert": "Critical processing error inside corporate mst daemon"},
        "transaction_id": "test-tx-discovery-999"
    })
    assert response.status_code == 200
    assert response.json()["parent_platform"] == "MST"
    assert "analyzer-mst" in response.json()["analyzer_target_url"]
"""
)

print("\n--- [PART 6 OF 10: PLATFORM DISCOVERY SERVICE COMPLETED] ---")
