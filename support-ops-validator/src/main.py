from fastapi import FastAPI
from pydantic import BaseModel
from src.evaluator import EvaluatorCriticEngine

app = FastAPI(title="Support Ops Audit Validator Interface", version="1.0.0")
engine = EvaluatorCriticEngine()

class ValidatorPayload(BaseModel):
    transaction_id: str
    execution_logs: list
    payload: dict

@app.post("/validate")
async def run_validation(data: ValidatorPayload):
    return await engine.validate_and_comment(data.transaction_id, data.execution_logs, data.payload)

@app.get("/healthz")
def health():
    return {"status": "healthy"}
