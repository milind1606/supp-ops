import httpx
import os

class AnsibleTowerClient:
    def __init__(self):
        self.endpoint = os.getenv("ANSIBLE_TOWER_URL", "http://mock-infrastructure-services:8001/api/v2/job_templates/launch")

    async def execute_playbook(self, playbook_name: str, host: str) -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                payload = {
                    "playbook_name": playbook_name,
                    "limit_host": host
                }
                response = await client.post(self.endpoint, json=payload)
                if response.status_code == 200:
                    return response.json()
                return {
                    "status": "failed",
                    "error": f"Automation edge engine returned bad status code: {response.status_code}"
                }
            except Exception as e:
                return {
                    "status": "failed",
                    "error": f"Connection exception during automation dispatch: {str(e)}"
                }
