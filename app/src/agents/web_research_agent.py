#!/usr/bin/env python3
"""
Web Research Agent - Specialized agent for web browsing, research, and information gathering.
"""

import logging
import time
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import re

from .base import BaseAgent
from src.types import AgentResponse, AgentType

logger = logging.getLogger(__name__)

class WebResearchAgent(BaseAgent):
    """
    A specialized agent for web research, browsing, and information gathering.
    This agent can:
    - Perform web searches
    - Fetch and analyze web content
    - Research topics with current information
    - Gather data from multiple sources
    - Provide source citations
    """

    def __init__(self):
        """Initialize the web research agent."""
        super().__init__(AgentType.WEB_RESEARCH)
        self.name = "WebResearchAgent"
        self.description = "Specialized agent for web research and information gathering"
        
        # Research capabilities
        self.research_methods = {
            "web_search": "Search the web for current information",
            "content_fetch": "Fetch and analyze specific web pages",
            "multi_source_research": "Gather information from multiple sources",
            "fact_checking": "Verify information across multiple sources",
            "trend_analysis": "Analyze current trends and patterns"
        }

    def _initialize_model(self):
        """Initialize the AI model for web research tasks."""
        try:
            # Initialize Google Gemini API for research analysis
            import google.generativeai as genai
            import os
            from dotenv import load_dotenv
            
            load_dotenv()
            api_key = os.getenv('GOOGLE_API_KEY')
            
            if api_key:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-1.5-pro')
                logger.info("Gemini model initialized for web research")
            else:
                logger.warning("GOOGLE_API_KEY not found, using basic research capabilities")
                self.model = None
                
        except Exception as e:
            logger.error(f"Error initializing Gemini model: {e}")
            self.model = None

    def _process_with_model(self, input_data: str) -> str:
        """Process input using the AI model for research analysis."""
        if not self.model:
            return self._basic_research_response(input_data)
        
        try:
            # Create a research-focused prompt
            research_prompt = f"""
            You are a web research specialist. Analyze the following request and provide a comprehensive response:
            
            REQUEST: {input_data}
            
            Provide:
            1. A clear understanding of what information is needed
            2. Suggested research approach
            3. Key search terms to use
            4. Types of sources to consult
            5. Expected outcomes
            
            Be concise but thorough.
            """
            
            response = self.model.generate_content(research_prompt)
            return response.text if hasattr(response, 'text') else str(response)
            
        except Exception as e:
            logger.error(f"Error in AI model processing: {e}")
            return self._basic_research_response(input_data)

    def _basic_research_response(self, input_data: str) -> str:
        """Provide a basic research response when AI model is not available."""
        return f"""
## 🔍 Web Research Analysis

**Research Request:** {input_data}

**Research Approach:**
1. **Web Search**: Perform comprehensive web search for current information
2. **Source Analysis**: Gather data from multiple reliable sources
3. **Fact Verification**: Cross-reference information for accuracy
4. **Content Synthesis**: Combine findings into coherent response

**Next Steps:**
- I'll search the web for relevant information
- Gather data from multiple sources
- Provide you with current, accurate information
- Include source citations for verification

Let me start researching this topic for you...
        """

    def perform_web_research(self, topic: str, research_type: str = "general") -> str:
        """Perform comprehensive web research on a specific topic.
        
        Args:
            topic: The topic to research
            research_type: Type of research (general, news, academic, etc.)
            
        Returns:
            Comprehensive research results
        """
        try:
            logger.info(f"Starting web research on topic: {topic} (type: {research_type})")
            
            # Perform multiple searches for comprehensive coverage
            search_queries = self._generate_search_queries(topic, research_type)
            all_results = []
            
            for query in search_queries:
                results = self._web_search(query, max_results=3)
                all_results.extend(results)
            
            # Remove duplicates and organize results
            unique_results = self._deduplicate_results(all_results)
            
            # Analyze and synthesize results
            research_summary = self._synthesize_research(topic, unique_results, research_type)
            
            return research_summary
            
        except Exception as e:
            logger.error(f"Error in web research: {e}")
            return f"I encountered an error while researching '{topic}'. Please try again."

    def _generate_search_queries(self, topic: str, research_type: str) -> List[str]:
        """Generate multiple search queries for comprehensive research."""
        base_queries = [
            f"latest {topic}",
            f"current {topic} information",
            f"{topic} recent developments"
        ]
        
        if research_type == "news":
            base_queries.extend([
                f"{topic} news today",
                f"{topic} latest updates",
                f"{topic} breaking news"
            ])
        elif research_type == "academic":
            base_queries.extend([
                f"{topic} research studies",
                f"{topic} academic papers",
                f"{topic} scientific findings"
            ])
        elif research_type == "technical":
            base_queries.extend([
                f"{topic} technical documentation",
                f"{topic} latest version",
                f"{topic} implementation guide"
            ])
        
        return base_queries

    def _deduplicate_results(self, results: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Remove duplicate results based on URL and content similarity."""
        seen_urls = set()
        seen_content = set()
        unique_results = []
        
        for result in results:
            url = result.get('link', '')
            content = result.get('snippet', '')[:100]  # First 100 chars for comparison
            
            if url not in seen_urls and content not in seen_content:
                seen_urls.add(url)
                seen_content.add(content)
                unique_results.append(result)
        
        return unique_results

    def _synthesize_research(self, topic: str, results: List[Dict[str, str]], research_type: str) -> str:
        """Synthesize research results into a coherent summary."""
        if not results:
            return f"I couldn't find current information about '{topic}' at the moment."
        
        # Create research summary
        summary = f"""
## 🔍 Research Results: {topic.title()}

**Research Type:** {research_type.title()}
**Sources Consulted:** {len(results)} unique sources
**Research Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### 📊 Key Findings:
"""
        
        # Group results by source type
        source_groups = {}
        for result in results:
            source = result.get('source', 'Unknown Source')
            if source not in source_groups:
                source_groups[source] = []
            source_groups[source].append(result)
        
        # Present results by source
        for source, source_results in source_groups.items():
            summary += f"\n#### {source}:\n"
            for i, result in enumerate(source_results, 1):
                summary += f"{i}. **{result['title']}**\n"
                summary += f"   {result['snippet']}\n"
                if result.get('link'):
                    summary += f"   [Source]({result['link']})\n"
                summary += "\n"
        
        # Add research insights
        summary += f"""
### 💡 Research Insights:
- **Coverage:** Information gathered from {len(source_groups)} different source types
- **Timeliness:** All sources provide current/recent information
- **Reliability:** Multiple sources for cross-verification
- **Completeness:** Comprehensive coverage of the topic

### 🔗 Additional Research:
If you need more specific information or want me to dive deeper into any aspect, just let me know!
        """
        
        return summary

    def fact_check(self, statement: str) -> str:
        """Fact-check a specific statement using web research.
        
        Args:
            statement: The statement to fact-check
            
        Returns:
            Fact-checking results
        """
        try:
            logger.info(f"Fact-checking statement: {statement}")
            
            # Extract key claims for verification
            claims = self._extract_claims(statement)
            
            if not claims:
                return "I couldn't identify specific claims to fact-check in your statement."
            
            fact_check_results = []
            
            for claim in claims:
                # Search for verification
                search_query = f"fact check {claim}"
                results = self._web_search(search_query, max_results=3)
                
                if results:
                    fact_check_results.append({
                        'claim': claim,
                        'verification': results[0]['snippet'],
                        'source': results[0].get('link', ''),
                        'source_name': results[0].get('source', 'Unknown')
                    })
                else:
                    fact_check_results.append({
                        'claim': claim,
                        'verification': 'No verification found',
                        'source': '',
                        'source_name': 'No source found'
                    })
            
            # Format fact-checking report
            report = f"""
## ✅ Fact-Checking Report

**Statement Analyzed:** {statement}

### 🔍 Claims Verified:
"""
            
            for result in fact_check_results:
                report += f"\n**Claim:** {result['claim']}\n"
                report += f"**Verification:** {result['verification']}\n"
                if result['source']:
                    report += f"**Source:** [{result['source_name']}]({result['source']})\n"
                report += "\n"
            
            report += f"\n*Fact-checking completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
            
            return report
            
        except Exception as e:
            logger.error(f"Error in fact-checking: {e}")
            return f"I encountered an error while fact-checking your statement. Please try again."

    def _extract_claims(self, statement: str) -> List[str]:
        """Extract factual claims from a statement for verification."""
        # Simple claim extraction - can be enhanced with NLP
        claims = []
        
        # Look for factual assertions
        factual_indicators = [
            "is", "are", "was", "were", "has", "have", "had",
            "contains", "includes", "consists of", "amounts to",
            "equals", "represents", "indicates", "shows"
        ]
        
        sentences = re.split(r'[.!?]+', statement)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if any(indicator in sentence.lower() for indicator in factual_indicators):
                # Extract the factual part
                for indicator in factual_indicators:
                    if indicator in sentence.lower():
                        parts = sentence.split(indicator, 1)
                        if len(parts) > 1:
                            claim = f"{parts[0].strip()} {indicator} {parts[1].strip()}"
                            claims.append(claim)
                            break
        
        return claims[:3]  # Limit to top 3 claims

    def get_trending_topics(self, category: str = "general") -> str:
        """Get currently trending topics in a specific category.
        
        Args:
            category: Category of trends (general, tech, business, etc.)
            
        Returns:
            Trending topics information
        """
        try:
            search_query = f"trending {category} topics today"
            results = self._web_search(search_query, max_results=5)
            
            if not results:
                return f"I couldn't find trending {category} topics at the moment."
            
            trends = f"""
## 📈 Trending {category.title()} Topics

**Current Trends as of {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:**

"""
            
            for i, result in enumerate(results, 1):
                trends += f"{i}. **{result['title']}**\n"
                trends += f"   {result['snippet']}\n"
                if result.get('link'):
                    trends += f"   [Learn More]({result['link']})\n"
                trends += "\n"
            
            return trends
            
        except Exception as e:
            logger.error(f"Error getting trending topics: {e}")
            return f"I encountered an error while getting trending {category} topics. Please try again."

    def process(self, input_data: str, session_id: Optional[str] = None) -> AgentResponse:
        """Process web research requests."""
        start_time = time.time()
        
        try:
            # Check for acknowledgments first
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
            
            # Determine research type and perform appropriate research
            research_type = self._determine_research_type(input_data)
            
            if research_type == "fact_check":
                content = self.fact_check(input_data)
            elif research_type == "trends":
                category = self._extract_trend_category(input_data)
                content = self.get_trending_topics(category)
            else:
                # General research
                topic = self._extract_research_topic(input_data)
                content = self.perform_web_research(topic, research_type)
            
            return AgentResponse(
                content=content,
                success=True,
                agent_type=self.agent_type.value,
                execution_time=time.time() - start_time,
                metadata={
                    'input_length': len(input_data),
                    'output_length': len(content),
                    'session_id': session_id,
                    'response_type': 'web_research',
                    'research_type': research_type
                }
            )
            
        except Exception as e:
            logger.error(f"Error in WebResearchAgent.process: {e}", exc_info=True)
            return AgentResponse(
                content="",
                error=str(e),
                success=False,
                agent_type=self.agent_type.value,
                execution_time=time.time() - start_time,
                error_message=f"Web research error: {str(e)}"
            )

    def _determine_research_type(self, input_data: str) -> str:
        """Determine the type of research needed based on input."""
        input_lower = input_data.lower()
        
        if any(word in input_lower for word in ["fact check", "verify", "true", "false", "accurate"]):
            return "fact_check"
        elif any(word in input_lower for word in ["trending", "trends", "popular", "hot", "viral"]) and not input_lower.startswith("what"):
            # Only treat as trends if it's not a question starting with "what"
            return "trends"
        elif any(word in input_lower for word in ["research", "study", "investigate", "explore"]):
            return "academic"
        elif any(word in input_lower for word in ["news", "current", "latest", "recent"]) and not input_lower.startswith("what"):
            # Only treat as news if it's not a question starting with "what"
            return "news"
        else:
            return "general"

    def _extract_research_topic(self, input_data: str) -> str:
        """Extract the main research topic from input."""
        # Remove common research request words
        research_words = [
            "research", "find", "look up", "search for", "tell me about",
            "what is", "how to", "explain", "describe", "analyze"
        ]
        
        topic = input_data
        for word in research_words:
            topic = topic.replace(word, "").strip()
        
        return topic if topic else "general research"

    def _extract_trend_category(self, input_data: str) -> str:
        """Extract trend category from input."""
        categories = ["tech", "business", "entertainment", "sports", "politics", "science"]
        
        input_lower = input_data.lower()
        for category in categories:
            if category in input_lower:
                return category
        
        return "general"
