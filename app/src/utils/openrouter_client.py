"""
OpenRouter API Client
Unified interface for accessing multiple AI models through OpenRouter
"""

import os
import logging
import time
from typing import Optional, Dict, Any, List, Union
import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class OpenRouterClient:
    """Client for interacting with OpenRouter API"""

    BASE_URL = "https://openrouter.ai/api/v1"

    # Recommended models by use case
    MODELS = {
        "content_creation": "anthropic/claude-3.5-sonnet",  # Best for creative writing
        "data_analysis": "anthropic/claude-3.5-sonnet",     # Excellent reasoning
        "devops": "anthropic/claude-3.5-sonnet",            # Technical tasks
        "customer_service": "anthropic/claude-3-haiku",     # Fast, cost-effective
        "web_research": "perplexity/llama-3.1-sonar-huge-128k-online",  # Built-in search
        "general": "anthropic/claude-3.5-sonnet",           # General purpose

        # Fallback options
        "fallback_1": "openai/gpt-4-turbo",
        "fallback_2": "anthropic/claude-3-opus",
        "fallback_3": "google/gemini-pro-1.5",
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenRouter client

        Args:
            api_key: OpenRouter API key (defaults to OPENROUTER_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            logger.warning("OpenRouter API key not found. Set OPENROUTER_API_KEY environment variable.")

        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        })

        # Optional: Add your app info for better analytics
        app_name = os.getenv('APP_NAME', 'MultiAgentAI21')
        app_url = os.getenv('APP_URL', 'https://multiagentai21.com')
        self.session.headers.update({
            'HTTP-Referer': app_url,
            'X-Title': app_name,
        })

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        fallback_models: Optional[List[str]] = None,
        **kwargs
    ) -> Union[Dict[str, Any], Any]:
        """
        Create a chat completion using OpenRouter

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model identifier (defaults to general model)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            frequency_penalty: Frequency penalty (-2 to 2)
            presence_penalty: Presence penalty (-2 to 2)
            fallback_models: List of fallback model IDs
            **kwargs: Additional parameters

        Returns:
            Response dict or streaming generator
        """
        model = model or self.MODELS["general"]

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": stream,
        }

        # Add optional parameters
        if max_tokens:
            payload["max_tokens"] = max_tokens
        if top_p is not None:
            payload["top_p"] = top_p
        if top_k is not None:
            payload["top_k"] = top_k
        if frequency_penalty is not None:
            payload["frequency_penalty"] = frequency_penalty
        if presence_penalty is not None:
            payload["presence_penalty"] = presence_penalty

        # Add fallback models for reliability
        if fallback_models:
            payload["route"] = "fallback"
            payload["models"] = [model] + fallback_models

        # Merge any additional parameters
        payload.update(kwargs)

        try:
            response = self._make_request(
                "POST",
                "/chat/completions",
                json=payload,
                stream=stream
            )

            if stream:
                return self._handle_stream(response)
            else:
                return response.json()

        except Exception as e:
            logger.error(f"OpenRouter API error: {e}")
            raise

    def generate_content(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Simple content generation (compatible with Gemini interface)

        Args:
            prompt: User prompt
            model: Model identifier
            system_prompt: Optional system message
            **kwargs: Additional parameters

        Returns:
            Generated text content
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        response = self.chat_completion(messages=messages, model=model, **kwargs)

        # Extract content from response
        if response and "choices" in response and len(response["choices"]) > 0:
            return response["choices"][0]["message"]["content"]

        raise Exception("Failed to generate content from OpenRouter")

    def _make_request(
        self,
        method: str,
        endpoint: str,
        stream: bool = False,
        **kwargs
    ) -> requests.Response:
        """
        Make HTTP request to OpenRouter API with retry logic

        Args:
            method: HTTP method
            endpoint: API endpoint path
            stream: Whether to stream response
            **kwargs: Additional request parameters

        Returns:
            Response object
        """
        url = f"{self.BASE_URL}{endpoint}"
        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                response = self.session.request(
                    method,
                    url,
                    stream=stream,
                    **kwargs
                )

                # Check for rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', retry_delay))
                    logger.warning(f"Rate limited. Retrying after {retry_after}s...")
                    time.sleep(retry_after)
                    continue

                # Raise for other errors
                response.raise_for_status()
                return response

            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise

                logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff

        raise Exception("Max retries exceeded")

    def _handle_stream(self, response: requests.Response):
        """
        Handle streaming response from OpenRouter

        Args:
            response: Streaming response object

        Yields:
            Parsed chunks from the stream
        """
        import json

        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]
                    if data == '[DONE]':
                        break
                    try:
                        chunk = json.loads(data)
                        yield chunk
                    except json.JSONDecodeError:
                        continue

    def list_models(self) -> List[Dict[str, Any]]:
        """
        Get list of available models from OpenRouter

        Returns:
            List of model information dicts
        """
        try:
            response = self._make_request("GET", "/models")
            return response.json().get("data", [])
        except Exception as e:
            logger.error(f"Failed to fetch models: {e}")
            return []

    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific model

        Args:
            model_id: Model identifier

        Returns:
            Model information dict or None
        """
        models = self.list_models()
        for model in models:
            if model.get("id") == model_id:
                return model
        return None


class OpenRouterAdapter:
    """
    Adapter to make OpenRouter compatible with existing Gemini-based code
    """

    def __init__(self, use_case: str = "general"):
        """
        Initialize adapter with recommended model for use case

        Args:
            use_case: Type of task (content_creation, data_analysis, etc.)
        """
        self.client = OpenRouterClient()
        self.use_case = use_case
        self.model = OpenRouterClient.MODELS.get(use_case, OpenRouterClient.MODELS["general"])

        # Set up fallbacks
        self.fallback_models = [
            OpenRouterClient.MODELS["fallback_1"],
            OpenRouterClient.MODELS["fallback_2"],
        ]

    def generate_content(self, prompt, **kwargs) -> "GenerationResponse":
        """
        Generate content (Gemini-compatible interface)

        Args:
            prompt: User prompt (str) or list of Gemini-format messages
            **kwargs: Additional parameters

        Returns:
            GenerationResponse object with text attribute
        """
        try:
            # Handle both string prompts and Gemini-format message lists
            if isinstance(prompt, list):
                # Convert Gemini format to OpenRouter format
                messages = []
                for msg in prompt:
                    if not isinstance(msg, dict) or 'role' not in msg:
                        continue

                    role = msg['role']
                    # Convert Gemini "model" role to OpenRouter "assistant" role
                    if role == 'model':
                        role = 'assistant'

                    # Extract content from "parts" array (Gemini format)
                    if 'parts' in msg and isinstance(msg['parts'], list) and len(msg['parts']) > 0:
                        content = msg['parts'][0] if isinstance(msg['parts'][0], str) else str(msg['parts'][0])
                    elif 'content' in msg:
                        content = msg['content']
                    else:
                        continue

                    messages.append({"role": role, "content": content})

                # Use chat_completion for multi-message conversations
                response = self.client.chat_completion(
                    messages=messages,
                    model=self.model,
                    **kwargs
                )

                # Extract text from OpenRouter response
                if response and "choices" in response and len(response["choices"]) > 0:
                    text = response["choices"][0]["message"]["content"]
                    return GenerationResponse(text)
                else:
                    raise Exception("No response from OpenRouter")
            else:
                # Simple string prompt
                text = self.client.generate_content(
                    prompt=prompt,
                    model=self.model,
                    **kwargs
                )
                return GenerationResponse(text)
        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            raise

    def chat_completion(self, messages: List[Dict[str, str]], **kwargs):
        """
        Chat completion with fallback support

        Args:
            messages: List of messages
            **kwargs: Additional parameters

        Returns:
            Response dict
        """
        return self.client.chat_completion(
            messages=messages,
            model=self.model,
            **kwargs
        )


class GenerationResponse:
    """Response object compatible with Gemini's response format"""

    def __init__(self, text: str):
        self.text = text

    def __str__(self):
        return self.text


# Convenience function for easy migration
def configure_openrouter(api_key: Optional[str] = None):
    """
    Configure OpenRouter globally (similar to genai.configure)

    Args:
        api_key: OpenRouter API key
    """
    if api_key:
        os.environ['OPENROUTER_API_KEY'] = api_key

    logger.info("OpenRouter configured successfully")


def GenerativeModel(use_case: str = "general"):
    """
    Factory function to create OpenRouter adapter (Gemini-compatible)

    Args:
        use_case: Type of task or model name

    Returns:
        OpenRouterAdapter instance
    """
    # Map common Gemini model names to use cases
    model_map = {
        "gemini-1.5-flash": "general",
        "gemini-1.5-pro": "content_creation",
        "gemini-pro": "general",
    }

    use_case = model_map.get(use_case, use_case)
    return OpenRouterAdapter(use_case)
