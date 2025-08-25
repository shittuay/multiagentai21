from dataclasses import dataclass
from typing import Any, Dict, Optional
from enum import Enum


class AgentType(str, Enum):
    """Types of agents available in the system."""
    AUTOMATION = "automation_of_complex_processes"
    DATA_ANALYSIS = "data_analysis_and_insights"
    CUSTOMER_SERVICE = "customer_service_and_engagement"
    CONTENT_CREATION = "content_creation_and_generation"
    


@dataclass
class AgentResponse:
    """Response from an agent."""
    content: str
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    success: bool = True
    agent_type: Optional[str] = None
    execution_time: float = 0.0
    error_message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    agent_name: Optional[str] = None 