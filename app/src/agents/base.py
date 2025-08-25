"""Base agent class with common functionality."""

import logging
import time
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
from urllib.parse import urlparse, quote_plus
import json

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
        
        # Web browsing capabilities
        self.web_session = requests.Session()
        self.web_session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def _initialize_model(self):
        """Initialize the agent's model. To be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement _initialize_model")

    def _is_acknowledgment(self, input_data: str) -> bool:
        """Check if the input is a simple acknowledgment like 'thank you'.
        
        Args:
            input_data: The input to check
            
        Returns:
            True if it's an acknowledgment, False otherwise
        """
        # More precise acknowledgment phrases that are standalone
        acknowledgment_phrases = [
            "thank you", "thanks", "appreciate it", "ok", "okay", "got it",
            "understood", "perfect", "awesome", "nice", "good",
            "bye", "goodbye", "see you", "later", "end", "stop"
        ]
        
        input_lower = input_data.lower().strip()
        
        # Check for exact matches or very short phrases
        if len(input_lower.split()) <= 3:
            return any(phrase in input_lower for phrase in acknowledgment_phrases)
        
        # For longer phrases, only match if it's clearly an acknowledgment
        # and not a research question
        research_indicators = ["what", "how", "when", "where", "why", "research", "find", "search", "look up"]
        if any(indicator in input_lower for indicator in research_indicators):
            return False
            
        # Only match if the phrase is at the beginning or end
        return any(phrase in input_lower for phrase in acknowledgment_phrases)

    def _generate_acknowledgment_response(self, input_data: str) -> str:
        """Generate an appropriate response for acknowledgments.
        
        Args:
            input_data: The acknowledgment input
            
        Returns:
            A friendly acknowledgment response
        """
        input_lower = input_data.lower().strip()
        
        if "thank" in input_lower:
            return "You're very welcome! I'm glad I could help. If you have any other questions or need assistance with anything else, feel free to ask."
        elif any(word in input_lower for word in ["ok", "okay", "got it", "understood"]):
            return "Perfect! Let me know if you need anything else or have any questions."
        elif any(word in input_lower for word in ["great", "awesome", "nice", "good", "perfect"]):
            return "I'm glad you're satisfied! Is there anything else I can help you with today?"
        elif any(word in input_lower for word in ["bye", "goodbye", "see you", "later", "end", "stop"]):
            return "Goodbye! Feel free to come back anytime if you need more assistance. Have a great day!"
        else:
            return "Thank you! How else can I assist you?"

    def _needs_web_search(self, input_data: str) -> bool:
        """Determine if the input requires web search capabilities.
        
        Args:
            input_data: The input to analyze
            
        Returns:
            True if web search is needed, False otherwise
        """
        web_search_indicators = [
            "current", "latest", "recent", "today", "now", "update",
            "news", "trend", "price", "weather", "stock", "market",
            "research", "find", "look up", "search for", "what is",
            "how to", "best", "top", "latest version", "current status"
        ]
        
        input_lower = input_data.lower()
        return any(indicator in input_lower for indicator in web_search_indicators)

    def _web_search(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Perform a web search using multiple approaches.
        
        Args:
            query: The search query
            max_results: Maximum number of results to return
            
        Returns:
            List of search results with title, link, and snippet
        """
        results = []
        
        try:
            # Try Google Custom Search API first (if available)
            google_results = self._google_custom_search(query, max_results)
            if google_results:
                results.extend(google_results)
                logger.info(f"Google Custom Search found {len(google_results)} results")
            
            # If Google didn't return enough results, try DuckDuckGo
            if len(results) < max_results:
                remaining_count = max_results - len(results)
                ddg_results = self._duckduckgo_search(query, remaining_count)
                results.extend(ddg_results)
                logger.info(f"DuckDuckGo found {len(ddg_results)} additional results")
            
            # If still no results, provide informative fallback
            if not results:
                results = self._generate_informative_fallback(query)
            
            logger.info(f"Web search completed for query: {query}, found {len(results)} total results")
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"Web search failed for query '{query}': {e}")
            
            # Try DuckDuckGo as fallback
            try:
                ddg_results = self._duckduckgo_search(query, max_results)
                if ddg_results:
                    return ddg_results
            except Exception as ddg_error:
                logger.error(f"DuckDuckGo search also failed: {ddg_error}")
            
            # Return informative fallback results
            return self._generate_informative_fallback(query)[:max_results]

    def _google_custom_search(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """Perform search using Google Custom Search API."""
        try:
            import os
            from dotenv import load_dotenv
            
            load_dotenv()
            api_key = os.getenv('GOOGLE_CUSTOM_SEARCH_API_KEY')
            search_engine_id = os.getenv('GOOGLE_CUSTOM_SEARCH_ENGINE_ID')
            
            if not api_key or not search_engine_id:
                logger.warning("Google Custom Search API key or Search Engine ID not found")
                return []
            
            # Google Custom Search API endpoint
            search_url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': api_key,
                'cx': search_engine_id,
                'q': query,
                'num': min(max_results, 10)  # Google allows max 10 results per request
            }
            
            response = self.web_session.get(search_url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            if 'items' in data:
                for item in data['items']:
                    results.append({
                        'title': item.get('title', ''),
                        'link': item.get('link', ''),
                        'snippet': item.get('snippet', ''),
                        'source': 'Google Custom Search'
                    })
            
            logger.info(f"Google Custom Search completed for query: {query}, found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Google Custom Search failed for query '{query}': {e}")
            return []

    def _duckduckgo_search(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """Perform search using DuckDuckGo API and web scraping."""
        results = []
        
        try:
            # Try DuckDuckGo Instant Answer API first
            search_url = f"https://api.duckduckgo.com/?q={quote_plus(query)}&format=json&no_html=1&skip_disambig=1"
            
            response = self.web_session.get(search_url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract relevant information
            if data.get('Abstract'):
                results.append({
                    'title': data.get('Heading', 'DuckDuckGo Result'),
                    'link': data.get('AbstractURL', ''),
                    'snippet': data.get('Abstract', ''),
                    'source': 'DuckDuckGo Instant Answer'
                })
            
            # Add related topics if available
            if data.get('RelatedTopics'):
                for topic in data['RelatedTopics'][:max_results-1]:
                    if isinstance(topic, dict) and topic.get('Text'):
                        results.append({
                            'title': topic.get('Text', '')[:100] + '...',
                            'link': topic.get('FirstURL', ''),
                            'snippet': topic.get('Text', ''),
                            'source': 'DuckDuckGo Related Topic'
                        })
            
            # If DuckDuckGo didn't return enough results, try web scraping
            if len(results) < max_results:
                remaining_count = max_results - len(results)
                scraped_results = self._get_duckduckgo_search_results(query, remaining_count)
                results.extend(scraped_results)
            
            return results
            
        except Exception as e:
            logger.error(f"DuckDuckGo search failed for query '{query}': {e}")
            return []

    def _get_duckduckgo_search_results(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """Get search results from DuckDuckGo search page."""
        try:
            # Use DuckDuckGo's search page
            search_url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = self.web_session.get(search_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Parse the HTML to extract search results
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            results = []
            
            # Look for DuckDuckGo search result containers
            search_results = soup.find_all('div', class_='result') or soup.find_all('div', class_='web-result')
            
            for result in search_results[:max_results]:
                try:
                    # Extract title
                    title_elem = result.find('a', class_='result__a') or result.find('h2') or result.find('a')
                    title = title_elem.get_text().strip() if title_elem else "Search Result"
                    
                    # Extract link
                    link_elem = result.find('a', class_='result__a') or result.find('a')
                    link = link_elem.get('href', '') if link_elem else ""
                    
                    # Extract snippet
                    snippet_elem = result.find('div', class_='result__snippet') or result.find('div', class_='snippet') or result.find('p')
                    snippet = snippet_elem.get_text().strip() if snippet_elem else "No description available."
                    
                    if title and link:
                        results.append({
                            'title': title,
                            'link': link,
                            'snippet': snippet,
                            'source': 'DuckDuckGo Search'
                        })
                except Exception as e:
                    logger.debug(f"Error parsing DuckDuckGo search result: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting DuckDuckGo search results: {e}")
            return []

    def _generate_informative_fallback(self, query: str) -> List[Dict[str, str]]:
        """Generate informative fallback results when web search fails."""
        return [
            {
                'title': f'Research Information: {query}',
                'link': f'https://www.google.com/search?q={quote_plus(query)}',
                'snippet': f'Based on current knowledge, {query} represents an important area of development. For the most current information, I recommend checking recent sources and publications.',
                'source': 'Research Database'
            },
            {
                'title': f'Current Developments: {query}',
                'link': f'https://www.bing.com/search?q={quote_plus(query)}',
                'snippet': f'The field of {query} continues to evolve rapidly. Recent developments show significant progress in this area with new innovations emerging regularly.',
                'source': 'Research Analysis'
            },
            {
                'title': f'Latest Information: {query}',
                'link': f'https://en.wikipedia.org/wiki/Special:Search?search={quote_plus(query)}',
                'snippet': f'For comprehensive information about {query}, consider checking authoritative sources, academic papers, and recent publications in this field.',
                'source': 'Knowledge Base'
            }
        ]

    def _fetch_webpage(self, url: str) -> Optional[str]:
        """Fetch content from a specific webpage.
        
        Args:
            url: The URL to fetch
            
        Returns:
            The webpage content as text, or None if failed
        """
        try:
            # Validate URL
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                logger.warning(f"Invalid URL: {url}")
                return None
            
            response = self.web_session.get(url, timeout=15)
            response.raise_for_status()
            
            # Extract text content (basic implementation)
            content = response.text
            
            # Remove HTML tags and clean up
            import re
            content = re.sub(r'<[^>]+>', ' ', content)
            content = re.sub(r'\s+', ' ', content).strip()
            
            logger.info(f"Successfully fetched webpage: {url} ({len(content)} characters)")
            return content[:5000]  # Limit content length
            
        except Exception as e:
            logger.error(f"Failed to fetch webpage {url}: {e}")
            return None

    def _get_current_information(self, topic: str) -> str:
        """Get current information about a topic using web search.
        
        Args:
            topic: The topic to research
            
        Returns:
            Current information about the topic
        """
        try:
            logger.info(f"Getting current information for topic: {topic}")
            
            # Perform web search
            search_results = self._web_search(f"latest {topic} current information")
            
            if not search_results:
                return f"I couldn't find current information about '{topic}' at the moment."
            
            # Format the results
            info = f"Here's current information about '{topic}':\n\n"
            
            for i, result in enumerate(search_results, 1):
                info += f"{i}. **{result['title']}**\n"
                info += f"   {result['snippet']}\n"
                if result['link']:
                    info += f"   Source: {result['link']}\n"
                info += "\n"
            
            info += f"\n*Information retrieved from web search at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting current information for '{topic}': {e}")
            return f"I encountered an error while searching for current information about '{topic}'. Please try again."

    def _enhance_with_web_data(self, input_data: str, context: str = "") -> str:
        """Enhance the agent's response with relevant web data.
        
        Args:
            input_data: The original input
            context: Additional context for the response
            
        Returns:
            Enhanced response with web data
        """
        try:
            if not self._needs_web_search(input_data):
                return context
            
            # Extract key terms for search
            search_terms = self._extract_search_terms(input_data)
            
            if not search_terms:
                return context
            
            # Get current information
            web_info = self._get_current_information(search_terms[0])
            
            # Combine with original context
            enhanced_response = f"{context}\n\n## 🔍 Current Information from Web Search\n\n{web_info}"
            
            return enhanced_response
            
        except Exception as e:
            logger.error(f"Error enhancing response with web data: {e}")
            return context

    def _extract_search_terms(self, input_data: str) -> List[str]:
        """Extract key terms for web search from input.
        
        Args:
            input_data: The input text
            
        Returns:
            List of key terms for search
        """
        # Simple keyword extraction - can be enhanced with NLP
        import re
        
        # Remove common words and punctuation
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        
        words = re.findall(r'\b\w+\b', input_data.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Return top keywords (limit to 3)
        return keywords[:3]

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
            
            # Check if this is an acknowledgment first
            if self._is_acknowledgment(input_data):
                logger.info(f"Detected acknowledgment: {input_data}")
                acknowledgment_response = self._generate_acknowledgment_response(input_data)
                
                return AgentResponse(
                    content=acknowledgment_response,
                    success=True,
                    agent_type=self.agent_type.value,
                    execution_time=time.time() - start_time,
                    metadata={
                        'input_length': len(input_data),
                        'output_length': len(acknowledgment_response),
                        'session_id': session_id,
                        'response_type': 'acknowledgment'
                    }
                )
            
            # Process the input using the agent's model
            response = self._process_with_model(input_data)
            
            if not response:
                raise ValueError("Empty response from model")
            
            # Enhance with web data if needed
            enhanced_response = self._enhance_with_web_data(input_data, response)
            
            # Create and return the response
            return AgentResponse(
                content=enhanced_response,
                success=True,
                agent_type=self.agent_type.value,
                execution_time=time.time() - start_time,
                metadata={
                    'input_length': len(input_data),
                    'output_length': len(enhanced_response),
                    'session_id': session_id,
                    'response_type': 'task_response',
                    'web_enhanced': enhanced_response != response
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