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
