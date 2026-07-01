import os
from pathlib import Path

def make_file(path: str, content: str):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"📦 Initialised: {path}")

# ==========================================
# CENTRALIZED ENVIRONMENT REQUIREMENT DEFINITIONS
# ==========================================

requirements_txt = """
fastapi==0.111.0
uvicorn==0.30.1
pydantic==2.7.4
langchain==0.2.5
langchain-core==0.2.9
langchain-aws==0.1.11
langgraph==0.1.4
langserve==0.2.2
llama-index-core==0.10.50
llama-index-vector-stores-amazon-opensearch==0.1.5
redis==5.0.7
requests==2.32.3
pytest==8.2.2
httpx==0.27.0
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

# ==========================================
# REPOSITORIES FOR KNOWLEDGE BASES & TOPOLOGIES
# ==========================================

# 1. Topology Registry File Definitions
make_file(
    "topoloy-all-systems/topoloy-all-systems.txt",
    """
=== ENTRY ===
HOSTNAME:hkgmcp003lx|ENVIRONMENT:envp-hk-shared|PARENT-PLATFORM:MCP
=== ENTRY ===
HOSTNAME:SYDMST031lx|ENVIRONMENT:envp-mbk|PARENT-PLATFORM:MST
=== ENTRY ===
HOSTNAME:lonmcp001lx|ENVIRONMENT:envd-uk-dev|PARENT-PLATFORM:MCP
=== ENTRY ===
HOSTNAME:nycmst012lx|ENVIRONMENT:envb-us-prod|PARENT-PLATFORM:MST
"""
)

make_file(
    "topoloy-all-systems/reademe.md",
    """
# Master Repository for Internal Topology Mappings
Contains server infrastructure mappings to evaluate parent asset platforms.
Sync Command: `aws s3 sync . s3://$KB_BUCKET_NAME/topoloy-all-systems/`
"""
)

# 2. MCP Platform Knowledge Base Definitions
make_file(
    "mcp_knowledge_base/past_incident_resolutions.txt",
    """
=== INCIDENT ===
ALERT: MCP Disk Out of Space on hkgmcp003lx
RESOLUTION: Trigger Ansible playbook `clean_temp_directories`. Target host `hkgmcp003lx`.
TIMESTAMP: 2026-06-15T12:00:00Z

=== INCIDENT ===
ALERT: MCP Connection Timeout on lonmcp001lx
RESOLUTION: Trigger Ansible playbook `restart_mcp_broker`. Target host `lonmcp001lx`.
TIMESTAMP: 2026-06-28T08:30:00Z
"""
)

make_file(
    "mcp_knowledge_base/server_mappings.txt",
    """
HOSTNAME:hkgmcp003lx|QUEUE:mcp.hongkong.core|OWNER:mcp-ops
HOSTNAME:lonmcp001lx|QUEUE:mcp.london.dev|OWNER:mcp-dev
"""
)

make_file(
    "mcp_knowledge_base/reademe.md",
    """
# MCP Operational Knowledge Base
Internal runbooks and data pipeline target streams for MCP instances.
Sync Command: `aws s3 sync . s3://$KB_BUCKET_NAME/mcp_knowledge_base/`
"""
)

# 3. MST Platform Knowledge Base Definitions
make_file(
    "mst_knowledge_base/past_incident_resolutions.txt",
    """
=== INCIDENT ===
ALERT: MST Memory Leak on SYDMST031lx
RESOLUTION: Trigger Ansible playbook `flush_redis_cache`. Target host `SYDMST031lx`.
TIMESTAMP: 2026-06-29T14:22:00Z

=== INCIDENT ===
ALERT: MST Service Crash on nycmst012lx
RESOLUTION: Trigger Ansible playbook `restart_mst_daemon`. Target host `nycmst012lx`.
TIMESTAMP: 2026-06-30T22:11:00Z
"""
)

make_file(
    "mst_knowledge_base/server_mappings.txt",
    """
HOSTNAME:SYDMST031lx|QUEUE:mst.sydney.prod|OWNER:mst-ops
HOSTNAME:nycmst012lx|QUEUE:mst.newyork.backup|OWNER:mst-infra
"""
)

make_file(
    "mst_knowledge_base/reademe.md",
    """
# MST Operational Knowledge Base
Internal runbooks and data pipeline target streams for MST instances.
Sync Command: `aws s3 sync . s3://$KB_BUCKET_NAME/mst_knowledge_base/`
"""
)

print("\n--- [PART 1 OF 10: BASELINE KNOWLEDGE STRUCTURING COMPLETED] ---")
