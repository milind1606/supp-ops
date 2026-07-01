from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class TicketPayload(BaseModel):
    alert: str = Field(..., description="The telemetry tool alert name or critical criteria")
    ticket_description: str = Field(..., description="Context extracted directly from the system ticket content")
    additional_context: Optional[str] = Field(None, description="Optional cluster configuration parameters")
    application_name: str = Field(..., description="Target parent system runtime application identifier")

class ExecutionResponse(BaseModel):
    transaction_id: str
    status: str
    summary: str
    resolution_details: Dict[str, Any]
