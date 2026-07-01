import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from src.main import app

# Instantiate the standard FastAPI TestClient layout
client = TestClient(app)

def test_ansible_trigger_health_probe():
    """Verifies that the Ansible trigger application readiness endpoint functions correctly."""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@patch("src.client.httpx.AsyncClient")
@pytest.mark.asyncio
async def test_ansible_playbook_successful_execution_dispatch(mock_async_client_class):
    """Audits successful mapping and delivery of structural payloads to the automation engine."""
    # Create an asynchronous network mock instance matching the client context manager
    mock_client_instance = AsyncMock()
    mock_async_client_class.return_value.__aenter__.return_value = mock_client_instance
    
    # Configure the mocked response to mirror an Ansible Tower job launch success
    mock_client_instance.post.return_value = AsyncMock(
        status_code=200,
        json=lambda: {
            "status": "successful",
            "job_id": 48291,
            "playbook": "clean_temp_directories",
            "target": "hkgmcp003lx",
            "output": "PLAY [Remediation Task] \\nchanged: [hkgmcp003lx]"
        }
    )

    # Package the incoming multi-agent orchestration state context tracking structure
    payload = {
        "analyzer_output": {
            "inferred_playbook": "clean_temp_directories",
            "target_host": "hkgmcp003lx"
        },
        "transaction_id": "TX-ANSIBLE-TEST-101"
    }

    # Execute the test payload run against the exposed microservice endpoint
    response = client.post("/execute", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["execution_status"] == "successful"
    assert data["job_id"] == 48291
    assert data["playbook_dispatched"] == "clean_temp_directories"
    assert data["target_node"] == "hkgmcp003lx"
    assert "PLAY [Remediation Task]" in data["raw_log"]

@patch("src.client.httpx.AsyncClient")
@pytest.mark.asyncio
async def test_ansible_playbook_network_failure_handling(mock_async_client_class):
    """Verifies that the edge microservice gracefully degrades and catches exception bubbles."""
    mock_client_instance = AsyncMock()
    mock_async_client_class.return_value.__aenter__.return_value = mock_client_instance
    
    # Force the mock network client block to trigger an explicit transport connection exception
    mock_client_instance.post.side_effect = Exception("Connection refused by automation master endpoint node.")

    payload = {
        "analyzer_output": {
            "inferred_playbook": "flush_redis_cache",
            "target_host": "SYDMST031lx"
        },
        "transaction_id": "TX-ANSIBLE-FAIL-202"
    }

    response = client.post("/execute", json=payload)
    
    # Confirm that the application caught the error safely and returned a clean failure structure
    assert response.status_code == 200
    data = response.json()
    assert data["execution_status"] == "failed"
    assert data["job_id"] is None
    assert "Connection exception" in data["raw_log"]
