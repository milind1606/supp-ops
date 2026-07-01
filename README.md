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





# Docker 
## following command to assemble and run all containers simultaneously in background daemon mode
docker compose up --build -d

## Ensure all distributed nodes have safely cleared internal execution checks:
docker compose ps


## Fire a sample infrastructure ticket down to your exposed local REST interface port 8000. This triggers the full sequential runtime workflow across all containers instantly:
curl -X POST http://localhost:8000/api/v1/tickets \
  -H "Content-Type: application/json" \
  -d '{
    "alert": "MST Memory Leak on SYDMST031lx",
    "ticket_description": "Production caching boundaries exceeded, service experiencing high latency",
    "application_name": "JIRA-PROD-SUPPORT-88"
  }'


# To sweep away local running instances and free system networking ports cleanly:
docker compose down -v
