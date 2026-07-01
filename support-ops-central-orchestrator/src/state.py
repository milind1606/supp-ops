from typing import TypedDict, List, Dict, Any, Optional

class SupportOpsTransactionState(TypedDict):
    """
    Unified transaction state tracking schema utilized by the LangGraph compilation 
    engine to pass execution contexts safely across microservice agent boundaries.
    """
    alert: str
    ticket_description: str
    additional_context: Optional[str]
    application_name: str  # Serves as the primary transaction tracking token identifier (tx)
    analysis_output: Dict[str, Any]
    ansible_status: str
    ansible_output: Dict[str, Any]
    validation_status: str
    jira_comment: str
    execution_logs: List[str]
