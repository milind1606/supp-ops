import os
import httpx
from langchain_aws import ChatBedrock

class EvaluatorCriticEngine:
    def __init__(self):
        self.llm = ChatBedrock(
            model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
            region_name=os.getenv("AWS_BEDROCK_REGION", "us-east-1")
        )
        self.jira_template = os.getenv("JIRA_COMMENT_URL_TEMPLATE", "http://mock-infrastructure-services:8001/rest/api/2/issue/{issue_key}/comment")

    async def validate_and_comment(self, tx_id: str, logs: list, payload: dict) -> dict:
        # Reconstruct the holistic multi-agent transaction execution trace footprint
        log_str = "\n".join([f"[{item.get('agent')}]: {item.get('message')}" for item in logs])
        
        system_prompt = (
            "You are a Senior Infrastructure Quality Auditor Validation Agent.\n"
            "Review the multi-agent logs execution trace against system infrastructure runbooks.\n"
            "Determine if the transaction has been successfully completed or failed.\n"
            "Output your absolute verdict starting precisely with [STATUS]: SUCCESS or [STATUS]: FAILED.\n"
            "Follow up with a clear summary section titled [SUMMARY]."
        )
        
        user_message = f"Transaction ID: {tx_id}\nInput context parameters: {payload}\n\nExecution Logs Trace:\n{log_str}"
        
        response = self.llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ])
        
        analysis = response.content
        status = "SUCCESS" if "[STATUS]: SUCCESS" in analysis else "FAILED"
        
        summary_text = "Automated multi-agent remediation workflow executed."
        if "[SUMMARY]" in analysis:
            summary_text = analysis.split("[SUMMARY]")[-1].strip()

        # Update Jira issue tracking system with the final comment entry
        issue_key = payload.get("application_name", "SUPPORT-KEY-101")
        await self._post_jira_comment(issue_key, tx_id, status, summary_text)

        return {"status": status, "summary": summary_text}

    async def _post_jira_comment(self, issue_key: str, tx_id: str, status: str, summary: str):
        url = self.jira_template.format(issue_key=issue_key)
        jira_body = {
            "body": f"[Multi-Agent System Central Audit Trail]\nTransaction: {tx_id}\nStatus: {status}\nResolution Summary: {summary}"
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                await client.post(url, json=jira_body)
            except Exception:
                pass # Safeguard execution path from downstream tracking network issues
