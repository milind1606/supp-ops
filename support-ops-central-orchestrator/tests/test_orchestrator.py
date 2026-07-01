import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Intercept external structural imports before loading the application engine context
with patch('redis.Redis'), patch('langchain_aws.ChatBedrock'):
    from src.main import app

client = TestClient(app)

def test_healthz_endpoint_liveness():
    """Verifies that the target pod health probes operate within parameters."""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@patch("src.orchestrator.redis.Redis")
@patch("src.orchestrator.httpx.Client")
def test_orchestrator_graph_workflow_routing(mock_httpx_class, mock_redis_class):
    """Audits the multi-agent graph step transition logic via structural network mocks."""
    
    # 1. Setup isolated mock client components
    mock_redis = MagicMock()
    mock_redis_class.return_value = mock_redis
    mock_redis.lrange.return_value = [b'{"agent": "Orchestrator", "status": "Mocked Activity Trace"}']
    
    mock_http_client = MagicMock()
    mock_httpx_class.return_value.__enter__.return_value = mock_http_client
    
    # 2. Simulate subsequent cluster microservice REST interface responses
    mock_discovery_response = MagicMock(status_code=200)
    mock_discovery_response.json.return_value = {
        "parent_platform": "MCP", 
        "analyzer_target_url": "http://support-ops-alert-analyzer-mcp:8001/analyze"
    }
    
    mock_analyzer_response = MagicMock(status_code=200)
    mock_analyzer_response.json.return_value = {
        "target_host": "hkgmcp003lx",
        "inferred_playbook": "clean_temp_directories"
    }
    
    mock_ansible_response = MagicMock(status_code=200)
    mock_ansible_response.json.return_value = {
        "execution_status": "successful"
    }
    
    mock_validator_response = MagicMock(status_code=200)
    mock_validator_response.json.return_value = {
        "status": "SUCCESS",
        "summary": "Verified automation execution signatures."
    }
    
    # Chain responses sequentially through the client execution pattern
    mock_http_client.post.side_effect = [
        mock_discovery_response,
        mock_analyzer_response,
        mock_ansible_response,
        mock_validator_response
    ]
    
    # 3. Compile transaction ticket payload properties
    payload = {
        "alert": "MCP Disk Out of Space on hkgmcp003lx",
        "ticket_description": "Log mount directory nearing full threshold capacity",
        "application_name": "JIRA-TICKET-OK-994"
    }
    
    # 4. Trigger test execution run
    response = client.post("/orchestrate", json=payload)
    
    assert response.status_code == 200
    assert response.json()["transaction_id"] == "JIRA-TICKET-OK-994"
    assert response.json()["status"] == "SUCCESS"
    assert "analysis_output" in response.json()["runtime_state"]
