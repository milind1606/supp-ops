import os
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from src.orchestrator import OrchestratorEngine

# Initialize the corporate core multi-agent microservice engine
app = FastAPI(
    title="Support-Ops Central Multi-Agent Orchestration Engine",
    version="1.0.0",
    description="EKS Fargate core runtime engine coordinating distributed support operations via LangGraph"
)

# Instantiate the state graph compilation engine instance
orchestrator = OrchestratorEngine()

# =====================================================================
# DATA VALIDATION CONTRACT SCHEMAS (Pydantic v2 Native)
# =====================================================================

class IngressTicketPayload(BaseModel):
    alert: str = Field(
        ..., 
        description="The raw target alert description string injected from telemetry monitoring tools"
    )
    ticket_description: str = Field(
        ..., 
        description="The textual engineering context extracted from ticket management interfaces"
    )
    additional_context: Optional[str] = Field(
        None, 
        description="Arbitrary configuration metadata injection properties"
    )
    application_name: str = Field(
        ..., 
        description="Target system application identity identifier or tracking ticket issue key string"
    )

class OrchestrationSuccessResponse(BaseModel):
    transaction_id: str
    status: str
    summary: str
    runtime_state: Dict[str, Any]

# =====================================================================
# DISTRIBUTED CORE HTTP ROUTING IMPLEMENTATIONS
# =====================================================================

@app.post(
    "/orchestrate", 
    response_model=OrchestrationSuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Triggers the distributed multi-agent support ticket resolution graph"
)
async def orchestrate_support_ticket(payload: IngressTicketPayload):
    """
    Ingests infrastructure alerts, runs physical topology platform discovery,
    routes contexts to specialized knowledge retrievers, dispatches remediation
    playbooks, and posts validation audits straight to target monitoring systems.
    """
    try:
        # Convert Pydantic state records safely to dict parameters
        input_data = payload.model_dump()
        
        # Dispatch transaction records directly through the LangGraph engine
        # This handles Redis stream logging, Platform Discovery, and downstream sub-agents
        final_graph_state = orchestrator.execute_workflow(input_data)
        
        # Extrapolate outcomes matching the centralized orchestrator structural contracts
        return OrchestrationSuccessResponse(
            transaction_id=payload.application_name,
            status=final_graph_state.get("validation_status", "FAILED"),
            summary=final_graph_state.get("jira_comment", "Remediation transaction completed validation loops."),
            runtime_state={
                "analysis_output": final_graph_state.get("analysis_output", {}),
                "ansible_status": final_graph_state.get("ansible_status", "UNKNOWN"),
                "ansible_output": final_graph_state.get("ansible_output", {}),
                "execution_logs": final_graph_state.get("execution_logs", [])
            }
        )
        
    except KeyError as ke:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Schema mapping contradiction inside transactional graph execution state: {str(ke)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Distributed multi-agent pipeline crash during runtime graph coordination: {str(e)}"
        )

@app.get(
    "/healthz", 
    status_code=status.HTTP_200_OK,
    summary="Liveness and readiness checking endpoint for AWS EKS target container probes"
)
def cluster_health_verification():
    return {
        "status": "healthy",
        "engine": "LangGraph Core Coordinator Cluster Node",
        "telemetry_linkage": "Active" if os.getenv("LANGCHAIN_TRACING_V2") == "true" else "Inactive"
    }

