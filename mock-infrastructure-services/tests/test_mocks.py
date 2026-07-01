from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_mock_ansible_endpoint():
    response = client.post("/api/v2/job_templates/launch", json={
        "playbook_name": "flush_redis_cache",
        "limit_host": "SYDMST031lx"
    })
    assert response.status_code == 200
    assert response.json()["status"] == "successful"

def test_mock_jira_endpoint():
    response = client.post("/rest/api/2/issue/SUPPORT-777/comment", json={
        "body": "Verification message"
    })
    assert response.status_code == 200
    assert "SUPPORT-777" in response.json()["issue"]
