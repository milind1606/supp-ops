import os
import httpx
import redis
import json
from langgraph.graph import StateGraph, END
from langchain_aws import ChatBedrock
from src.state import SupportOpsTransactionState

class OrchestratorEngine:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            decode_responses=True
        )
        
        # Microservice target topology endpoint bindings
        self.discovery_url = os.getenv("DISCOVERY_URL", "http://support-ops-platform-discovery:8001/discover")
        self.ansible_url = os.getenv("ANSIBLE_URL", "http://support-ops-ansible-trigger:8001/execute")
        self.validator_url = os.getenv("VALIDATOR_URL", "http://support-ops-validator:8001/validate")
        
        self.llm = ChatBedrock(model_id="anthropic.claude-3-5-sonnet-20240620-v1:0", region_name="us-east-1")
        self.workflow = self._compile_graph()

    def _log_to_redis_stream(self, tx_id: str, agent_name: str, status: str):
        self.redis_client.rpush(f"tx_logs:{tx_id}", json.dumps({"agent": agent_name, "status": status}))

    def analyze_ticket_step(self, state: SupportOpsTransactionState) -> SupportOpsTransactionState:
        tx = state["application_name"]
        
        # -----------------------------------------------------------------
        # STEP 1: INTERACTIVE PLATFORM DISCOVERY ROUTER
        # -----------------------------------------------------------------
        self._log_to_redis_stream(tx, "Orchestrator", "Routing transaction to Platform Discovery Agent")
        
        discovery_payload = {
            "payload": {
                "alert": state.get("alert", ""),
                "ticket_description": state["ticket_description"]
            },
            "transaction_id": tx
        }
        
        # Default analyzer route fallback parameters
        target_analyzer_url = os.getenv("MCP_ANALYZER_URL", "http://support-ops-alert-analyzer-mcp:8001/analyze")
        
        try:
            with httpx.Client(timeout=15.0) as client:
                disc_res = client.post(self.discovery_url, json=discovery_payload)
                disc_res.raise_for_status()
                disc_data = disc_res.json()
                
                # Extract dynamic target routing endpoints from discovery engine response
                target_analyzer_url = disc_data.get("analyzer_target_url", target_analyzer_url)
                state["execution_logs"].append(f"Platform Discovery finished: Identified platform {disc_data.get('parent_platform')}")
                self._log_to_redis_stream(tx, "Orchestrator", f"Discovery matched platform: {disc_data.get('parent_platform')}")
        except Exception as e:
            state["execution_logs"].append(f"Platform Discovery breakdown fallback used: {str(e)}")
            self._log_to_redis_stream(tx, "Orchestrator", f"Discovery service unavailable, choosing default fallback.")

        # -----------------------------------------------------------------
        # STEP 2: DYNAMIC ROUTED KNOWLEDGE BASE ANALYSIS
        # -----------------------------------------------------------------
        self._log_to_redis_stream(tx, "Orchestrator", "Routing context parameters to selected Alert Analyzer Agent")
        try:
            analyzer_payload = {
                "payload": {
                    "alert": state.get("alert", ""),
                    "ticket_description": state["ticket_description"]
                },
                "transaction_id": tx
            }
            with httpx.Client(timeout=30.0) as client:
                res = client.post(target_analyzer_url, json=analyzer_payload)
                res.raise_for_status()
                state["analysis_output"] = res.json()
                state["execution_logs"].append("Analyzer step finished successfully.")
        except Exception as e:
            state["analysis_output"] = {"HOST": "UNKNOWN", "ERROR": str(e)}
            state["execution_logs"].append(f"Analyzer step breakdown: {str(e)}")
        return state

    def trigger_ansible_step(self, state: SupportOpsTransactionState) -> SupportOpsTransactionState:
        tx = state["application_name"]
        analysis = state.get("analysis_output", {})
        
        # Check normalisation tracking metrics across both target hosts definitions
        host_verdict = analysis.get("target_host", "UNKNOWN")
        if host_verdict == "UNKNOWN" or analysis.get("HOST") == "UNKNOWN":
            self._log_to_redis_stream(tx, "Orchestrator", "Bypassing Ansible step: target host unknown")
            state["ansible_status"] = "SKIPPED"
            return state
            
        self._log_to_redis_stream(tx, "Orchestrator", "Routing execution map to Ansible Trigger Agent")
        try:
            payload = {
                "analyzer_output": analysis,
                "transaction_id": tx
            }
            with httpx.Client(timeout=30.0) as client:
                res = client.post(self.ansible_url, json=payload)
                res.raise_for_status()
                state["ansible_status"] = res.json().get("execution_status", "FAILED")
                state["ansible_output"] = res.json()
                state["execution_logs"].append("Ansible step executed successfully.")
        except Exception as e:
            state["ansible_status"] = "FAILED"
            state["execution_logs"].append(f"Ansible node crash details: {str(e)}")
        return state

    def validate_metrics_step(self, state: SupportOpsTransactionState) -> SupportOpsTransactionState:
        tx = state["application_name"]
        self._log_to_redis_stream(tx, "Orchestrator", "Routing current state execution trace to Validator Agent")
        redis_audit_trail = self.redis_client.lrange(f"tx_logs:{tx}", 0, -1)
        
        parsed_logs = []
        for entry in redis_audit_trail:
            try:
                parsed_logs.append(json.loads(entry))
            except Exception:
                parsed_logs.append({"agent": "UNKNOWN", "message": entry})

        try:
            payload = {
                "transaction_id": tx,
                "execution_logs": parsed_logs,
                "payload": {
                    "alert": state.get("alert", ""),
                    "ticket_description": state["ticket_description"],
                    "application_name": state["application_name"]
                }
            }
            with httpx.Client(timeout=30.0) as client:
                res = client.post(self.validator_url, json=payload)
                res.raise_for_status()
                state["validation_status"] = res.json().get("status", "FAILED")
                state["jira_comment"] = res.json().get("summary", "")
                state["execution_logs"].append("Validator step completed.")
        except Exception as e:
            state["validation_status"] = "FAILED"
            state["execution_logs"].append(f"Validator system failure: {str(e)}")
        return state

    def _compile_graph(self):
        gb = StateGraph(SupportOpsTransactionState)
        gb.add_node("analyzer", self.analyze_ticket_step)
        gb.add_node("ansible", self.trigger_ansible_step)
        gb.add_node("validator", self.validate_metrics_step)
        gb.set_entry_point("analyzer")
        gb.add_edge("analyzer", "ansible")
        gb.add_edge("ansible", "validator")
        gb.add_edge("validator", END)
        return gb.compile()

    def execute_workflow(self, initial_input: dict) -> dict:
        initial_state: SupportOpsTransactionState = {
            "alert": initial_input.get("alert", ""),
            "ticket_description": initial_input.get("ticket_description", ""),
            "additional_context": initial_input.get("additional_context", None),
            "application_name": initial_input.get("application_name", "UNKNOWN-TX"),
            "analysis_output": {},
            "ansible_status": "PENDING",
            "ansible_output": {},
            "validation_status": "PENDING",
            "jira_comment": "",
            "execution_logs": ["Workflow initiated via state machine architecture."]
        }
        return self.workflow.invoke(initial_state)
