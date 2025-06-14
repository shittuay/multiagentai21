"""Base agent class with common functionality."""

import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime

from src.types import AgentType, AgentResponse

logger = logging.getLogger(__name__)

class BaseAgent:
    """Base class for all agents."""

    def __init__(self, agent_type: AgentType):
        """Initialize base agent.
        
        Args:
            agent_type: Type of agent being initialized
        """
        self.agent_type = agent_type
        self.model = None
        self.session_id = None
        self._initialize_model()

    def _initialize_model(self):
        """Initialize the agent's model. To be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement _initialize_model")

    def process(self, input_data: str, session_id: Optional[str] = None) -> AgentResponse:
        """Process input data and generate a response.
        
        Args:
            input_data: The input to process
            session_id: Optional session ID for tracking
            
        Returns:
            AgentResponse containing the generated response
        """
        start_time = time.time()
        self.session_id = session_id
        
        try:
            logger.info(f"Processing input: {input_data[:100]}...")
            
            # Process the input using the agent's model
            response = self._process_with_model(input_data)
            
            if not response:
                raise ValueError("Empty response from model")
            
            # Create and return the response
            return AgentResponse(
                content=response,
                success=True,
                agent_type=self.agent_type.value,
                execution_time=time.time() - start_time,
                metadata={
                    'input_length': len(input_data),
                    'output_length': len(response),
                    'session_id': session_id
                }
            )
            
        except Exception as e:
            logger.error(f"Error in {self.__class__.__name__}.process: {e}", exc_info=True)
            return AgentResponse(
                content="",
                success=False,
                agent_type=self.agent_type.value,
                error=type(e).__name__,
                error_message=str(e),
                execution_time=time.time() - start_time,
                metadata={
                    'input_length': len(input_data),
                    'session_id': session_id,
                    'error_type': type(e).__name__
                }
            )

    def _process_with_model(self, input_data: str) -> str:
        """Process input using the agent's model. To be implemented by subclasses.
        
        Args:
            input_data: The input to process
            
        Returns:
            Processed response as a string
        """
        raise NotImplementedError("Subclasses must implement _process_with_model")

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the agent.
        
        Returns:
            Dictionary containing agent status information
        """
        return {
            'agent_type': self.agent_type.value,
            'model_initialized': self.model is not None,
            'session_id': self.session_id,
            'status': 'active' if self.model is not None else 'inactive'
        }

    def update_status(self, status: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Update the agent's status.
        
        Args:
            status: New status (e.g., 'active', 'inactive', 'error')
            metadata: Additional metadata about the status
        """
        logger.info(f"Updating {self.agent_type.value} agent status to {status}")
        # This will be implemented by the MultiAgentCodingAI class
        pass 