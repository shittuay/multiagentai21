import logging
import os
import google.generativeai as genai
from typing import Any, Dict, Optional
from abc import ABC, abstractmethod

# Assuming BaseAgent and AgentResponse are defined in src.types or src.agent_core
# If not, you might need to adjust these imports or define them here temporarily
try:
    from src.types import AgentType, AgentResponse, BaseAgent # Assuming AgentType and AgentResponse are here
except ImportError:
    # Fallback definitions if src.types cannot be imported directly (e.g., during testing or if structure differs)
    logging.warning("Could not import AgentType, AgentResponse, BaseAgent from src.types. Using fallback definitions.")
    from enum import Enum
    from dataclasses import dataclass

    class AgentType(Enum):
        AUTOMATION = "automation"
        DATA_ANALYSIS = "data_analysis"
        CUSTOMER_SERVICE = "customer_service"
        CONTENT_CREATION = "content_creation"

    @dataclass
    class AgentResponse:
        success: bool
        content: Optional[str] = None
        error: Optional[str] = None
        execution_time: Optional[float] = None
        agent_type: Optional[AgentType] = None
        tool_outputs: Optional[Dict[str, Any]] = None

    class BaseAgent(ABC):
        def __init__(self, agent_type: AgentType, model_name: str = "gemini-pro", google_api_key: Optional[str] = None):
            self.agent_type = agent_type
            self.model = self._initialize_model(model_name, google_api_key)

        def _initialize_model(self, model_name: str, api_key: Optional[str]):
            if not api_key:
                logging.error(f"GOOGLE_API_KEY not provided for {self.agent_type.value} agent.")
                return None
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(model_name)
                logging.info(f"Generative model '{model_name}' initialized for {self.agent_type.value} agent.")
                return model
            except Exception as e:
                logging.error(f"Failed to initialize generative model for {self.agent_type.value} agent: {e}", exc_info=True)
                return None

        @abstractmethod
        def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
            pass


logger = logging.getLogger(__name__)

class AutomationAgent(BaseAgent):
    """
    An agent specialized in providing information and solutions related to automation.
    It leverages a generative AI model to answer queries on automation strategies,
    tools, and workflows.
    """
    def __init__(self, google_api_key: Optional[str] = None):
        super().__init__(AgentType.AUTOMATION, model_name="gemini-pro", google_api_key=google_api_key)
        logger.info("AutomationAgent initialized and ready to process requests.")

    def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """
        Processes a query related to automation using the generative AI model.
        
        Args:
            query (str): The user's query about automation.
            context (Optional[Dict[str, Any]]): Additional context for the query (e.g., chat history).

        Returns:
            AgentResponse: The response containing the generated content or an error.
        """
        if not self.model:
            logger.error("Generative model is not initialized for AutomationAgent.")
            return AgentResponse(success=False, error="Automation agent is not ready. Model not initialized.")

        try:
            # Dynamically adjust prompt based on query content for better specificity
            platform_keywords = ["facebook", "twitter", "instagram", "linkedin", "social media", "social network"]
            is_social_media_query = any(keyword in query.lower() for keyword in platform_keywords)

            if is_social_media_query:
                system_instruction = "You are an expert social media automation consultant. Provide detailed and helpful information regarding the user's query about automating social media tasks, specifically for the mentioned platforms if any. Focus on tools, strategies, and best practices for social media automation. Keep your answer concise but informative."
            else:
                system_instruction = "You are an expert automation consultant. Provide detailed and helpful information regarding the user's query about automation. Keep your answer concise but informative."
            
            full_prompt = f"{system_instruction}\n\nUser query: {query}"
            
            # Incorporate chat history if available
            chat_history = context.get('chat_history', []) if context else []
            model_chat_history = []
            for msg in chat_history:
                role = "user" if msg["role"] == "user" else "model"
                # Ensure parts is a list of dicts, and content is in 'text' key
                model_chat_history.append({"role": role, "parts": [{"text": msg["content"]}]})
            
            # Start a chat session with the model
            chat = self.model.start_chat(history=model_chat_history)
            
            logger.info(f"Sending prompt to Gemini for Automation Agent: {full_prompt}")
            response = chat.send_message(full_prompt)
            
            # Extract content safely
            generated_content = response.text
            
            logger.info("Received response from Gemini for Automation Agent.")
            return AgentResponse(success=True, content=generated_content, agent_type=self.agent_type)

        except Exception as e:
            logger.error(f"Error processing automation query with Gemini: {e}", exc_info=True)
            return AgentResponse(success=False, error=f"Failed to generate automation response: {e}", agent_type=self.agent_type)

