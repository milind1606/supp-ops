import pytest
from unittest.mock import patch, MagicMock

# 1. Intercept and mock out AWS Bedrock before loading the FastAPI application
mock_bedrock_class = patch("langchain_aws.ChatBedrock").start()
mock_llm_instance = MagicMock()
mock_llm_instance.invoke.return_value.content = (
    "[STATUS]: SUCCESS\n"
    "[SUMMARY]: All multi-agent operational transactions matched system infrastructure runbooks successfully."
)
mock_bedrock_class.return_value = mock_llm_instance

# 2. Safely import app now that dependencies are globally patched
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_validator_health_probe():
    """Verifies that the Validator microservice liveness and readiness probe works."""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@patch("src.evaluator.httpx.AsyncClient")
def test_validator_critic_evaluation_and_jira_injection(mock_async_client_class):
    """Audits transaction log trace evaluation and outbound Jira API payload mapping."""
    # Create an async mock for the outbound Jira REST API client interface
    mock_http_client = MagicMock()
    mock_async_client_class.return_value.__aenter__.return_value = mock_http_client
    mock_http_client.post.return_value = MagicMock(status_code=200)

    # Compile a sample transaction trace payload matching the graph ledger state output
    payload = {
        "transaction_id": "TX-AUDIT-99001-OK",
        "execution_logs": [
            {"agent": "platform_discovery", "message": "Routed target parent platform: MCP"},
            {"agent": "alert_analyzer", "message": "Completed analysis over target host: hkgmcp003lx"},
            {"agent": "ansible_trigger", "message": "Remediation job triggered with status: successful"}
        ],
        "payload": {
            "alert": "MCP Disk Out of Space on hkgmcp003lx",
            "ticket_description": "Log mount directory space capacity threshold reached",
            "application_name": "SUPPORT-TICKET-CRITICAL-88"
        }
    }

    # Execute request run using standard blocking client (which handles async internally)
    response = client.post("/validate", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert "All multi-agent operational transactions" in data["summary"]

# Safely close downstream patches on suite completion
def teardown_module(module):
    patch.stopall()
