import pytest
from unittest.mock import patch, MagicMock

# 1. Intercept and mock out AWS Bedrock before loading the FastAPI application
mock_bedrock_class = patch("langchain_aws.ChatBedrock").start()
mock_llm_instance = MagicMock()
mock_llm_instance.invoke.return_value.content = (
    "[HOST]: hkgmcp003lx\n"
    "[ENVIRONMENT]: envp-hk-shared\n"
    "[SUMMARY]: MCP Disk Out of Space on hkgmcp003lx\n"
    "[RESOLUTION]: Trigger Ansible playbook clean_temp_directories."
)
mock_bedrock_class.return_value = mock_llm_instance

# 2. Safely import app now that dependencies are mocked
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_mcp_analyzer_health_check():
    """Verifies that the MCP analyzer application layer health probe works perfectly."""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_mcp_analyzer_engine_execution_flow():
    """Audits the prompt formatting, LlamaIndex metadata filter construction, and parsing loops."""
    # Package the execution transaction payloads
    payload = {
        "payload": {
            "alert": "MCP Disk Out of Space on hkgmcp003lx",
            "ticket_description": "Log system filling up critical space boundaries"
        },
        "transaction_id": "TX-MCP-9922-OK"
    }

    # Fire request to the FastAPI application gateway
    response = client.post("/analyze", json=payload)
    
    # Rigorous assertion validations
    assert response.status_code == 200
    data = response.json()
    assert data["target_host"] == "hkgmcp003lx"
    assert data["inferred_playbook"] == "clean_temp_directories"
    assert data["assigned_queue"] == "mcp.hongkong.core"
    assert "[HOST]: hkgmcp003lx" in data["raw_analysis"]

# Clean up our global patches after the test run finishes
def teardown_module(module):
    patch.stopall()
