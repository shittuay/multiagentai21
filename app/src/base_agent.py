#!/usr/bin/env python3
"""
Base Agent Class
Provides the foundation for all AI agents in the MultiAgentAI21 system
"""

import logging
import os
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

from src.types import AgentType

# Load environment variables from .env file with robust fallback
try:
    from src.utils.env_loader import ensure_env_loaded, get_api_key
    ensure_env_loaded()
except ImportError:
    # Fallback to simple load_dotenv if env_loader is not available
    load_dotenv()

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Base class for all agents with self-learning capabilities."""
    
    def __init__(self, agent_type: AgentType):
        """Initialize the base agent."""
        self.agent_type = agent_type
        self.model = None
        self.performance_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'average_response_time': 0.0,
            'user_satisfaction_scores': [],
            'common_failure_patterns': [],
            'improvement_suggestions': []
        }
        self.learning_history = []
        self.adaptive_prompts = {}
        self._initialize_model()

    def _initialize_model(self):
        """Initialize the AI model for the agent."""
        try:
            # Get API key using robust method with fallbacks
            try:
                from src.utils.env_loader import get_api_key
                api_key = get_api_key('GOOGLE_API_KEY')
            except ImportError:
                # Fallback to direct environment variable access
                api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
            
            if not api_key:
                logger.error("No valid API key found. Please set GOOGLE_API_KEY or GEMINI_API_KEY in your .env file")
                raise ValueError("API key is required. Please set GOOGLE_API_KEY environment variable")
            
            # Configure the Gemini API
            genai.configure(api_key=api_key)
            
            # Try different model names in order of preference
            model_names = ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro']
            
            for model_name in model_names:
                try:
                    self.model = genai.GenerativeModel(model_name)
                    # Test the model with a simple prompt
                    test_response = self.model.generate_content("Hello")
                    if test_response and hasattr(test_response, 'text'):
                        logger.info(f"Successfully initialized Gemini model: {model_name}")
                        return
                except Exception as e:
                    logger.warning(f"Failed to initialize model {model_name}: {e}")
                    continue
            
            # If all models fail, raise an error
            raise ValueError("Could not initialize any Gemini model. Please check your API key and model availability.")
            
        except Exception as e:
            logger.error(f"Error initializing model: {e}")
            raise

    def _process_with_model(self, prompt: str, chat_history: Optional[List[Dict]] = None) -> str:
        """Process prompt with the AI model, including chat history and learning."""
        start_time = time.time()
        
        try:
            if not self.model:
                raise ValueError("Model not initialized")
            
            # Apply adaptive prompt improvements
            enhanced_prompt = self._apply_adaptive_improvements(prompt)
            
            # Build the chat history for the model
            contents = []
            if chat_history:
                for message in chat_history:
                    if not message.get("content"):
                        continue
                    if "MultiAgentAI21 can make mistakes" in message["content"]:
                        continue

                    if message["role"] == "user":
                        contents.append({"role": "user", "parts": [message["content"]]})
                    elif message["role"] == "assistant":
                        contents.append({"role": "model", "parts": [message["content"]]})
            
            # Add the current prompt as the last user message
            contents.append({"role": "user", "parts": [enhanced_prompt]})
            
            # Use generate_content with the entire 'contents' list
            response = self.model.generate_content(contents)
            
            if hasattr(response, 'text') and response.text:
                response_text = response.text.strip()
                
                # Record performance metrics
                self._record_performance_metrics(True, time.time() - start_time)
                
                # Learn from this interaction
                self._learn_from_interaction(prompt, response_text, True, time.time() - start_time)
                
                return response_text
            elif hasattr(response, 'parts') and response.parts:
                response_text = ''.join([part.text for part in response.parts if hasattr(part, 'text')])
                
                # Record performance metrics
                self._record_performance_metrics(True, time.time() - start_time)
                
                # Learn from this interaction
                self._learn_from_interaction(prompt, response_text, True, time.time() - start_time)
                
                return response_text
            else:
                # Record failure
                self._record_performance_metrics(False, time.time() - start_time)
                return "Error: No text content in model response"
                
        except Exception as e:
            # Record failure
            self._record_performance_metrics(False, time.time() - start_time)
            logger.error(f"Error in _process_with_model: {e}")
            return f"Error processing request: {str(e)}"

    def _record_performance_metrics(self, success: bool, response_time: float):
        """Record performance metrics for the agent."""
        self.performance_metrics['total_requests'] += 1
        
        if success:
            self.performance_metrics['successful_requests'] += 1
        
        # Update average response time
        current_avg = self.performance_metrics['average_response_time']
        total_requests = self.performance_metrics['total_requests']
        self.performance_metrics['average_response_time'] = (
            (current_avg * (total_requests - 1) + response_time) / total_requests
        )

    def _learn_from_interaction(self, prompt: str, response: str, success: bool, response_time: float):
        """Learn from the interaction to improve future responses."""
        # Record the interaction
        self.learning_history.append({
            'prompt': prompt,
            'response': response,
            'success': success,
            'response_time': response_time,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 100 interactions
        if len(self.learning_history) > 100:
            self.learning_history = self.learning_history[-100:]
        
        # Learn from failures
        if not success:
            self.performance_metrics['improvement_suggestions'].append({
                'type': 'failure_analysis',
                'suggestion': f'Failed to process: {prompt[:100]}...',
                'timestamp': datetime.now().isoformat()
            })

    def _apply_adaptive_improvements(self, prompt: str) -> str:
        """Apply adaptive improvements to the prompt based on learning."""
        # Simple adaptive improvements - can be enhanced
        for pattern, improvement in self.adaptive_prompts.items():
            if pattern.lower() in prompt.lower():
                prompt = f"{improvement}\n\n{prompt}"
                break
        return prompt

    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report for the agent."""
        success_rate = (
            self.performance_metrics['successful_requests'] / 
            self.performance_metrics['total_requests']
            if self.performance_metrics['total_requests'] > 0 else 0.0
        )
        
        return {
            'agent_type': self.agent_type.value,
            'total_requests': self.performance_metrics['total_requests'],
            'success_rate': f"{success_rate:.2%}",
            'average_response_time': f"{self.performance_metrics['average_response_time']:.2f}s",
            'learning_history_size': len(self.learning_history),
            'improvement_suggestions': self.performance_metrics['improvement_suggestions'][-5:],  # Last 5
            'last_updated': datetime.now().isoformat()
        }

    def add_user_feedback(self, satisfaction_score: int, feedback_text: str = ""):
        """Add user feedback for continuous improvement."""
        if 1 <= satisfaction_score <= 5:
            self.performance_metrics['user_satisfaction_scores'].append({
                'score': satisfaction_score,
                'feedback': feedback_text,
                'timestamp': datetime.now().isoformat()
            })
            
            # Keep only last 50 feedback entries
            if len(self.performance_metrics['user_satisfaction_scores']) > 50:
                self.performance_metrics['user_satisfaction_scores'] = \
                    self.performance_metrics['user_satisfaction_scores'][-50:]
            
            # Learn from feedback
            if satisfaction_score < 3:  # Low satisfaction
                self.performance_metrics['improvement_suggestions'].append({
                    'type': 'user_feedback',
                    'suggestion': f'User feedback: {feedback_text}',
                    'timestamp': datetime.now().isoformat()
                })

    @abstractmethod
    def process(self, input_data: str, session_id: Optional[str] = None, **kwargs) -> Any:
        """Process input data and return a response."""
        pass

