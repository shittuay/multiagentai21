import json
import mimetypes
import os
import shutil
import tempfile
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Sequence, Union
import logging
import uuid
from datetime import datetime

import google.generativeai as genai
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
from google.cloud import aiplatform

from src.data_analysis import DataAnalyzer
from src.api.firestore import FirestoreClient
from src.types import AgentType, AgentResponse
from src.agents.content_creator import ContentCreatorAgent
from src.agents.enhanced_content_creator import EnhancedContentCreatorAgent

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FileType(Enum):
    """Supported file types for processing"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    SPREADSHEET = "spreadsheet"
    UNKNOWN = "unknown"


class BaseAgent(ABC):
    """Base class for all agents."""
    
    def __init__(self, agent_type: AgentType):
        """Initialize the base agent."""
        self.agent_type = agent_type
        self.model = None
        self._initialize_model()

    def _initialize_model(self):
        """Initialize the AI model for the agent."""
        try:
            # Get API key from environment variable
            api_key = os.getenv('GOOGLE_API_KEY')
            if not api_key:
                logger.error("GOOGLE_API_KEY environment variable not set")
                raise ValueError("GOOGLE_API_KEY environment variable is required")
            
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
        """Process prompt with the AI model, including chat history."""
        try:
            if not self.model:
                raise ValueError("Model not initialized")
            
            # Build the chat history for the model
            # Gemini's generate_content expects a list of {role: ..., parts: [...]}
            contents = []
            if chat_history:
                for message in chat_history:
                    # Skip empty content or initial system warnings from app.py
                    if not message.get("content"):
                        continue
                    if "MultiAgentAI21 can make mistakes" in message["content"]:
                        continue

                    # Map your 'user' and 'assistant' roles to Gemini's 'user' and 'model'
                    if message["role"] == "user":
                        contents.append({"role": "user", "parts": [message["content"]]})
                    elif message["role"] == "assistant":
                        contents.append({"role": "model", "parts": [message["content"]]})
            
            # Add the current prompt as the last user message
            contents.append({"role": "user", "parts": [prompt]})
            
            # Use generate_content with the entire 'contents' list
            response = self.model.generate_content(contents)
            
            if hasattr(response, 'text') and response.text:
                return response.text.strip()
            elif hasattr(response, 'parts') and response.parts:
                return ''.join([part.text for part in response.parts if hasattr(part, 'text')])
            else:
                logger.warning("No text content in model response")
                return "I received your request but couldn't generate a proper response."
                
        except Exception as e:
            logger.error(f"Error processing with model: {e}")
            
            # Provide helpful fallback responses based on the error
            if "404" in str(e) or "model" in str(e).lower():
                return """I'm experiencing technical difficulties with the AI model. Please try the following:

1. **Check your API key**: Ensure your GOOGLE_API_KEY is correctly set
2. **Verify model access**: Make sure you have access to the Gemini API
3. **Try again**: Sometimes temporary API issues resolve quickly
4. **Contact support**: If the issue persists, check the Google AI Studio status

In the meantime, here's a general approach to your request:
- Break down your request into smaller, specific questions
- Provide more context about what you're trying to achieve
- Consider using alternative tools or methods for your task"""
            
            elif "rate limit" in str(e).lower() or "quota" in str(e).lower():
                return "I've reached the API rate limit. Please wait a moment and try again, or consider upgrading your API quota."
            
            else:
                return f"I encountered an error while processing your request: {str(e)}. Please try again or rephrase your question."

    @abstractmethod
    def process(self, input_data: str, chat_history: Optional[List[Dict]] = None) -> AgentResponse: # ADDED chat_history
        """Process input data and return a response."""
        pass


class AnalysisAgent(BaseAgent):
    """Agent for data analysis tasks."""

    def __init__(self):
        """Initialize the analysis agent."""
        super().__init__(AgentType.DATA_ANALYSIS)
        self.analyzer = DataAnalyzer() if 'DataAnalyzer' in globals() else None

    def process(self, input_data: str, chat_history: Optional[List[Dict]] = None) -> AgentResponse: # ADDED chat_history
        """Process analysis requests."""
        start_time = time.time()
        
        try:
            if not input_data or not input_data.strip():
                return AgentResponse(
                    content="Please provide a valid analysis request.",
                    success=False,
                    agent_type=self.agent_type.value,
                    execution_time=time.time() - start_time
                )
            
            # For text-based analysis requests, use AI-powered analysis
            # The DataAnalyzer is designed for actual DataFrame data, not text queries
            analysis_prompt = f"""
            You are a professional data analyst with expertise in business intelligence, statistical analysis, and data visualization.
            
            TASK: Analyze the following data analysis request and provide actionable insights.
            
            REQUEST: {input_data}
            
            Please provide a comprehensive analysis including:
            
            1. **Data Understanding**: What type of data is being analyzed?
            2. **Key Metrics**: What are the most important metrics to track?
            3. **Trends & Patterns**: What patterns or trends should be identified?
            4. **Statistical Insights**: What statistical analysis would be most valuable?
            5. **Visualization Recommendations**: What charts/graphs would best represent this data?
            6. **Actionable Recommendations**: What specific actions should be taken based on the analysis?
            7. **Next Steps**: What additional analysis or data collection might be needed?
            
            Format your response with clear sections, bullet points, and specific recommendations.
            If the request mentions specific data types (sales, customer, financial, etc.), tailor your analysis accordingly.
            
            IMPORTANT: Provide specific, actionable advice that can be implemented immediately.
            """
            
            response_text = self._process_with_model(analysis_prompt, chat_history) # PASSED chat_history
            
            return AgentResponse(
                content=response_text,
                success=True,
                agent_type=self.agent_type.value,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Error in AnalysisAgent.process: {e}", exc_info=True)
            return AgentResponse(
                content="",
                error=str(e),
                success=False,
                agent_type=self.agent_type.value,
                execution_time=time.time() - start_time,
                error_message=f"Analysis error: {str(e)}"
            )


class ChatAgent(BaseAgent):
    """Agent for customer service interactions."""

    def __init__(self):
        """Initialize the customer service agent."""
        super().__init__(AgentType.CUSTOMER_SERVICE)
        # We will use the chat_history passed from app.py directly instead of self.conversation_history
        # This simplifies state management across app runs in Streamlit
        # self.conversation_history = [] # REMOVED: Managed by app.py's session_state

    # MODIFIED: Removed internal conversation_history management as app.py already handles it and passes it
    def process(self, input_data: str, chat_history: Optional[List[Dict]] = None) -> AgentResponse: # ADDED chat_history
        """Process customer service requests."""
        start_time = time.time()
        
        try:
            if not input_data or not input_data.strip():
                return AgentResponse(
                    content="Please provide a customer service request or question.",
                    success=False,
                    agent_type=self.agent_type.value,
                    execution_time=time.time() - start_time
                )
            
            # Check for simple acknowledgments first
            acknowledgment_phrases = [
                "thank you", "thanks", "appreciate it", "ok", "okay", "got it",
                "understood", "perfect", "great", "awesome", "nice", "good"
            ]
            
            if any(phrase in input_data.lower() for phrase in acknowledgment_phrases):
                # Provide simple, appropriate responses for acknowledgments
                if "thank" in input_data.lower():
                    response_text = "You're very welcome! I'm glad I could help. If you have any other questions or need assistance with anything else, feel free to ask."
                elif any(word in input_data.lower() for word in ["ok", "okay", "got it", "understood"]):
                    response_text = "Perfect! Let me know if you need anything else or have any questions."
                elif any(word in input_data.lower() for word in ["great", "awesome", "nice", "good", "perfect"]):
                    response_text = "I'm glad you're satisfied! Is there anything else I can help you with today?"
                else:
                    response_text = "Thank you! How else can I assist you?"
                
                return AgentResponse(
                    content=response_text,
                    success=True,
                    agent_type=self.agent_type.value,
                    execution_time=time.time() - start_time
                )
            
            # Use the passed chat_history directly
            # No need to append to self.conversation_history here

            # The _process_with_model will now handle converting chat_history to model's format
            
            # Enhanced customer service prompt with specific scenarios
            customer_service_prompt = f"""
            You are an expert customer service representative with deep knowledge of:
            - Product support and troubleshooting
            - Billing and payment issues
            - Account management
            - Technical support
            - Return and refund policies
            - Order tracking and shipping
            - General inquiries and complaints
            
            CUSTOMER REQUEST: {input_data}
            
            Please provide a professional, helpful response that:
            1. **Acknowledges the customer's concern** with empathy
            2. **Provides specific, actionable solutions** to their problem
            3. **Offers step-by-step guidance** when applicable
            4. **Includes relevant policies or procedures** if mentioned
            5. **Suggests escalation options** if the issue requires further assistance
            6. **Maintains a positive, professional tone** throughout
            
            If the customer mentions:
            - Technical issues: Provide troubleshooting steps
            - Billing problems: Explain payment options and procedures
            - Product questions: Give detailed product information
            - Complaints: Show understanding and offer solutions
            - Account issues: Guide through account management processes
            
            Always end with a clear next step or offer additional assistance.
            """
            
            response_text = self._process_with_model(customer_service_prompt, chat_history) # PASSED chat_history
            
            # No need to append response to self.conversation_history
            # The chat_history in app.py's session_state already gets the response

            # No need to keep conversation history manageable here, app.py manages it.
            
            return AgentResponse(
                content=response_text,
                success=True,
                agent_type=self.agent_type.value,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Error in ChatAgent.process: {e}", exc_info=True)
            return AgentResponse(
                content="",
                error=str(e),
                success=False,
                agent_type=self.agent_type.value,
                execution_time=time.time() - start_time,
                error_message=f"Customer service error: {str(e)}"
            )


class FileAgent(BaseAgent):
    """Agent for automation and workflow optimization."""

    def __init__(self):
        """Initialize the automation agent."""
        super().__init__(AgentType.AUTOMATION)

    def process(self, input_data: str, chat_history: Optional[List[Dict]] = None) -> AgentResponse: # ADDED chat_history
        """Process automation requests."""
        start_time = time.time()
        
        try:
            if not input_data or not input_data.strip():
                return AgentResponse(
                    content="Please provide a specific automation request or workflow optimization need.",
                    success=False,
                    agent_type=self.agent_type.value,
                    execution_time=time.time() - start_time
                )
            
            # Check for simple thank you or closing phrases
            thank_you_phrases = ["thank you", "thanks", "appreciate it", "ok", "okay", "got it"]
            if any(phrase in input_data.lower() for phrase in thank_you_phrases):
                return AgentResponse(
                    content="You're welcome! If you have any more automation or workflow optimization needs, feel free to ask.",
                    success=True,
                    agent_type=self.agent_type.value,
                    execution_time=time.time() - start_time
                )

            # Enhanced automation prompt with specific automation scenarios
            automation_prompt = f"""
            You are an expert automation engineer and workflow optimization specialist with expertise in:
            - Business process automation (BPA)
            - Robotic Process Automation (RPA)
            - Workflow design and optimization
            - Scripting and programming for automation
            - Integration between systems and applications
            - Data processing and ETL automation
            - Email and communication automation
            - File and document processing automation
            - Customer onboarding and offboarding workflows
            - Reporting and analytics automation
            
            AUTOMATION REQUEST: {input_data}
            
            Please provide a comprehensive automation solution that includes:
            
            1. **Process Analysis**: Break down the current process and identify automation opportunities
            2. **Technology Recommendations**: Suggest specific tools, platforms, or technologies
            3. **Implementation Steps**: Provide detailed step-by-step implementation guide
            4. **Code Examples**: Include relevant code snippets or scripts when applicable
            5. **Integration Points**: Identify where this automation connects with existing systems
            6. **Error Handling**: Plan for potential issues and how to handle them
            7. **Monitoring & Maintenance**: How to track performance and maintain the automation
            8. **ROI Considerations**: Expected time savings and efficiency improvements
            
            If the request involves:
            - File processing: Provide file handling and processing automation
            - Data workflows: Include data transformation and validation steps
            - Communication: Suggest email, messaging, or notification automation
            - Reporting: Include automated report generation and distribution
            - Customer processes: Design customer journey automation
            
            Format your response with clear sections, code blocks where appropriate, and specific actionable steps.
            """
            
            response_text = self._process_with_model(automation_prompt, chat_history) # PASSED chat_history

            return AgentResponse(
                content=response_text,
                success=True,
                agent_type=self.agent_type.value,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Error in FileAgent.process: {e}", exc_info=True)
            return AgentResponse(
                content="",
                error=str(e),
                success=False,
                agent_type=self.agent_type.value,
                execution_time=time.time() - start_time,
                error_message=f"Automation error: {str(e)}"
            )


class ContentCreatorAgent(BaseAgent):
    """Agent specialized in content creation and generation using Google Gemini API"""

    def __init__(self):
        """Initialize the content creator agent with Gemini API integration."""
        super().__init__(AgentType.CONTENT_CREATION)
        
        # Enhanced templates with more content types
        self.templates = {
            "blog_post": {
                "intro": "Write an engaging introduction that hooks the reader and clearly states the main topic. Include relevant statistics or trends if applicable.",
                "body": "Develop the main points with supporting evidence, examples, and expert insights. Use a mix of short and long paragraphs for readability.",
                "conclusion": "Summarize key takeaways and end with a clear, actionable call to action.",
                "format": "Use clear headings, short paragraphs, and bullet points where appropriate. Include relevant keywords for SEO."
            },
            "social_media": {
                "hook": "Start with an attention-grabbing statement, question, or trending topic reference.",
                "content": "Keep it concise, engaging, and platform-appropriate. Use emojis and line breaks for readability.",
                "call_to_action": "End with a clear call to action or question to encourage engagement.",
                "hashtags": "Include 3-5 relevant, trending hashtags for better visibility."
            },
            "article": {
                "headline": "Create a compelling headline that includes keywords and creates curiosity.",
                "subheadings": "Use clear, descriptive subheadings to break up content and improve readability.",
                "content": "Provide valuable information with a mix of facts, examples, expert quotes, and data points.",
                "format": "Use a mix of short and long paragraphs, lists, and visual elements. Include internal and external links where relevant."
            },
            "marketing_copy": {
                "headline": "Create a compelling headline that emphasizes value proposition.",
                "body": "Focus on benefits, use persuasive language, and include social proof.",
                "call_to_action": "Clear, urgent call to action with value proposition.",
                "format": "Concise, scannable, and focused on conversion."
            },
            "product_description": {
                "overview": "Clear, concise product overview highlighting key features.",
                "benefits": "Focus on customer benefits and use cases.",
                "specifications": "Technical details in an easy-to-read format.",
                "format": "Scannable with bullet points and clear sections."
            },
            "email_content": {
                "subject": "Attention-grabbing subject line with clear value proposition.",
                "greeting": "Personalized greeting based on recipient.",
                "body": "Clear, concise message with a single focus.",
                "closing": "Professional sign-off with clear next steps.",
                "format": "Short paragraphs, clear hierarchy, mobile-friendly."
            }
        }

    def process(self, input_data: str, chat_history: Optional[List[Dict]] = None) -> AgentResponse: # ADDED chat_history
        """Process content creation requests."""
        start_time = time.time()
        
        try:
            if not input_data or not input_data.strip():
                return AgentResponse(
                    content="Please provide a specific content creation request (e.g., 'Write a blog post about AI trends', 'Create social media content for a product launch', 'Draft an email newsletter').",
                    success=False,
                    agent_type=self.agent_type.value,
                    execution_time=time.time() - start_time
                )
            
            # Check if the user is asking for guidance on how to create content
            # Enhanced guidance detection with more specific patterns
            guidance_patterns = [
                "how to create",
                "how to write", 
                "guide on",
                "steps to create",
                "steps to write",
                "tell me about creating",
                "how do i create",
                "how do i write",
                "what are the steps",
                "guide me through",
                "explain how to",
                "tutorial on",
                "tips for creating",
                "best practices for"
            ]
            
            input_lower = input_data.lower().strip()
            is_guidance_request = any(pattern in input_lower for pattern in guidance_patterns)
            
            # Additional check: if the input starts with "HOW TO" (all caps), it's likely guidance
            if input_data.strip().startswith("HOW TO"):
                is_guidance_request = True

            if is_guidance_request:
                logger.info(f"Detected guidance request: {input_data}")
                # Pass the original input_data to guidance generator as it's the full context of the query
                return self._generate_guidance_content(input_data, start_time, chat_history) # PASSED chat_history

            # If it's not a guidance request, proceed to generate content
            # Analyze request to determine content type
            content_type = self._detect_content_type(input_data)
            
            # Extract the actual topic for content generation
            content_topic = self._extract_content_topic(input_data, content_type)
            logger.info(f"Detected content type: {content_type}, Extracted topic: {content_topic}")

            # Generate content based on type with enhanced prompts, using the extracted topic
            if content_type == "blog_post":
                response_text = self._generate_blog_post(content_topic, chat_history) # PASSED chat_history
            elif content_type == "social_media":
                response_text = self._generate_social_media_post(content_topic, chat_history) # PASSED chat_history
            elif content_type == "article":
                response_text = self._generate_article(content_topic, chat_history) # PASSED chat_history
            elif content_type == "marketing_copy":
                response_text = self._generate_marketing_copy(content_topic, chat_history) # PASSED chat_history
            elif content_type == "product_description":
                response_text = self._generate_product_description(content_topic, chat_history) # PASSED chat_history
            elif content_type == "email_content":
                response_text = self._generate_email_content(content_topic, chat_history) # PASSED chat_history
            else:
                response_text = self._generate_general_content(content_topic, chat_history) # PASSED chat_history
            
            # Add content type information to the response
            enhanced_response = f"""
## 📝 Content Type: {content_type.replace('_', ' ').title()}

{response_text}

---
*Generated by MultiAgentAI21 Content Creation Agent*
            """
            
            return AgentResponse(
                content=enhanced_response,
                success=True,
                agent_type=self.agent_type.value,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Error in ContentCreatorAgent.process: {e}", exc_info=True)
            return AgentResponse(
                content="",
                error=str(e),
                success=False,
                agent_type=self.agent_type.value,
                execution_time=time.time() - start_time,
                error_message=f"Content generation error: {str(e)}"
            )

    def _detect_content_type(self, request: str) -> str:
        """Detect the type of content to generate from the request."""
        request_lower = request.lower()
        
        if any(word in request_lower for word in ["blog", "blog post", "article post"]):
            return "blog_post"
        elif any(word in request_lower for word in ["social media", "tweet", "facebook", "instagram", "linkedin"]):
            return "social_media"
        elif any(word in request_lower for word in ["article", "news", "report"]):
            return "article"
        elif any(word in request_lower for word in ["marketing", "advertisement", "ad copy", "sales"]):
            return "marketing_copy"
        elif any(word in request_lower for word in ["product", "description", "feature"]):
            return "product_description"
        elif any(word in request_lower for word in ["email", "newsletter", "message"]):
            return "email_content"
        else:
            return "general"

    def _generate_blog_post(self, prompt: str, chat_history: Optional[List[Dict]] = None) -> str:
        """Generate a blog post using Gemini API."""
        # Strengthen the prompt to ensure the model adheres to the exact topic
        blog_prompt = f"""
        You are a professional content writer and SEO expert.
        
        **STRICTLY ADHERE TO THE FOLLOWING TOPIC**: {prompt}
        
        Create a comprehensive, engaging blog post. Do NOT deviate from this topic.
        
        REQUIREMENTS:
        1. **Headline**: Create a compelling, SEO-optimized headline (H1)
        2. **Introduction**: Hook the reader with a strong opening (2-3 paragraphs)
        3. **Main Content**: Develop 5-7 key points with supporting evidence
        4. **Subheadings**: Use clear H2 and H3 headings for structure
        5. **Examples & Data**: Include relevant statistics, case studies, or examples
        6. **Actionable Tips**: Provide practical advice readers can implement
        7. **Conclusion**: Summarize key takeaways with a clear call-to-action
        8. **SEO Elements**: Include relevant keywords naturally throughout
        9. **Length**: Target 800-1200 words
        10. **Tone**: Professional yet engaging, authoritative but accessible
        
        STRUCTURE:
        - Compelling headline
        - Engaging introduction with hook
        - Main content with clear sections
        - Practical examples and tips
        - Strong conclusion with CTA
        - Relevant internal/external links (mention where they should go)
        
        Format with proper markdown: # for H1, ## for H2, ### for H3, **bold** for emphasis, and bullet points where appropriate.
        """

        return self._process_with_model(blog_prompt, chat_history) # PASSED chat_history

    def _generate_social_media_post(self, prompt: str, chat_history: Optional[List[Dict]] = None) -> str: # ADDED chat_history
        """Generate a social media post using Gemini API."""
        social_prompt = f"""Create an engaging social media post about: {prompt}

Follow these guidelines:
1. Start with an attention-grabbing hook
2. Keep it concise and engaging
3. Use emojis and line breaks for readability
4. Include 3-5 relevant hashtags
5. End with a call to action
6. Make it shareable and engaging
7. Use a conversational tone

Format the response with emojis and hashtags."""

        return self._process_with_model(social_prompt, chat_history) # PASSED chat_history

    def _generate_article(self, prompt: str, chat_history: Optional[List[Dict]] = None) -> str: # ADDED chat_history
        """Generate an article using Gemini API."""
        article_prompt = f"""Write a detailed article about: {prompt}

Follow these guidelines:
1. Create a compelling headline
2. Include an executive summary
3. Use clear subheadings
4. Provide in-depth analysis with examples
3. Include expert quotes or insights
6. Add relevant statistics and data
7. End with actionable takeaways
8. Target length: 1500-2000 words
9. Maintain a professional tone
10. Optimize for SEO

Format the response with proper markdown structure."""

        return self._process_with_model(article_prompt, chat_history) # PASSED chat_history

    def _generate_marketing_copy(self, prompt: str, chat_history: Optional[List[Dict]] = None) -> str: # ADDED chat_history
        """Generate marketing copy using Gemini API."""
        marketing_prompt = f"""Create compelling marketing copy about: {prompt}

Follow these guidelines:
1. Focus on benefits and value proposition
2. Use persuasive language
3. Include social proof elements
4. Create urgency without being pushy
5. Use clear, compelling calls to action
6. Keep it concise and impactful
7. Maintain brand voice
8. Optimize for conversion

Format the response with clear sections and emphasis on key points."""

        return self._process_with_model(marketing_prompt, chat_history) # PASSED chat_history

    def _generate_product_description(self, prompt: str, chat_history: Optional[List[Dict]] = None) -> str: # ADDED chat_history
        """Generate product description using Gemini API."""
        product_prompt = f"""Write a detailed product description for: {prompt}

Follow these guidelines:
1. Start with a compelling overview
2. Highlight key features and benefits
3. Include technical specifications
4. Use clear, scannable formatting
5. Focus on customer value
6. Include use cases
7. Add social proof if available
8. End with a clear call to action

Format the response with clear sections and bullet points."""

        return self._process_with_model(product_prompt, chat_history) # PASSED chat_history

    def _generate_email_content(self, prompt: str, chat_history: Optional[List[Dict]] = None) -> str: # ADDED chat_history
        """Generate email content using Gemini API."""
        email_prompt = f"""Create an effective email about: {prompt}

Follow these guidelines:
1. Write an attention-grabbing subject line
2. Use a personalized greeting
3. Keep the message clear and concise
4. Focus on a single main point
5. Use a professional but engaging tone
6. Include a clear call to action
7. End with a professional sign-off
8. Optimize for mobile reading

Format the response with clear sections and proper email structure."""

        return self._process_with_model(email_prompt, chat_history) # PASSED chat_history

    def _generate_general_content(self, prompt: str, chat_history: Optional[List[Dict]] = None) -> str: # ADDED chat_history
        """Generate general content using Gemini API."""
        general_prompt = f"""Create engaging content about: {prompt}

Follow these guidelines:
1. Use clear, engaging language
2. Structure content logically
3. Include relevant examples
4. Maintain consistent tone
5. Use appropriate formatting
6. Focus on value for the reader
7. Include a clear conclusion
8. Optimize for readability

Format the response with proper structure and formatting."""

        return self._process_with_model(general_prompt, chat_history) # PASSED chat_history

    def _extract_content_topic(self, request: str, content_type: str) -> str:
        """Extracts the core topic from a content creation request."""
        request_lower = request.lower()
        topic = request
        
        # Define common prefixes for content generation requests
        prefixes = {
            "blog_post": ["write a blog post about", "create a blog post about", "blog post on"],
            "social_media": ["create a social media post about", "write a social media post for", "social media content for"],
            "article": ["write an article about", "create an article on", "article on"],
            "marketing_copy": ["create marketing copy about", "write marketing copy for", "marketing copy for"],
            "product_description": ["write a product description for", "create a product description for", "product description for"],
            "email_content": ["write an email about", "create an email for", "email content for"],
            "general": ["create content about", "write about", "generate content on"]
        }
        
        # Try to remove the most relevant prefix
        for prefix in prefixes.get(content_type, []):
            if request_lower.startswith(prefix):
                topic = request[len(prefix):].strip()
                break
        
        # Further clean-up if the topic still contains leading "about" or "on"
        if topic.lower().startswith("about "):
            topic = topic[len("about "):].strip()
        if topic.lower().startswith("on "):
            topic = topic[len("on "):].strip()
            
        return topic

    def _generate_guidance_content(self, prompt: str, start_time: float, chat_history: Optional[List[Dict]] = None) -> AgentResponse: # ADDED chat_history
        """Generate guidance on how to create content."""
        guidance_prompt = f"""
        You are an expert content strategist and a helpful guide.
        
        TASK: Provide step-by-step guidance on how to fulfill the following content creation request:
        
        REQUEST: {prompt}
        
        Focus on explaining the process, best practices, and key considerations for creating this type of content, rather than creating the content itself.
        
        Include:
        1.  **Planning**: What steps are involved in planning this content?
        2.  **Structure**: What is a typical structure or outline?
        3.  **Key Elements**: What are the essential components to include?
        4.  **Tone & Style**: What kind of tone or style is appropriate?
        5.  **Tools/Tips**: Any recommended tools or general tips?
        6.  **Optimization**: How can this content be optimized (e.g., for SEO, engagement)?
        
        Provide a detailed, clear, and actionable guide.
        """
        response_text = self._process_with_model(guidance_prompt, chat_history) # PASSED chat_history
        
        return AgentResponse(
            content=f"## 💡 Guidance on Content Creation\n\n{response_text}\n\n---\n*Guidance by MultiAgentAI21 Content Creation Agent*",
            success=True,
            agent_type=self.agent_type.value,
            execution_time=time.time() - start_time
        )


def create_agent(agent_type: AgentType) -> BaseAgent:
    """Create an agent of the specified type."""
    try:
        if agent_type == AgentType.CONTENT_CREATION:
            # Try to use enhanced agent first, fall back to basic
            try:
                # Ensure EnhancedContentCreatorAgent is imported or defined
                if 'EnhancedContentCreatorAgent' in globals():
                    return EnhancedContentCreatorAgent()
                else:
                    raise ImportError("EnhancedContentCreatorAgent not found in globals.")
            except (ImportError, NameError) as e:
                logger.warning(f"EnhancedContentCreatorAgent not available: {e}, using basic ContentCreatorAgent")
                return ContentCreatorAgent()
        elif agent_type == AgentType.DATA_ANALYSIS:
            return AnalysisAgent()
        elif agent_type == AgentType.CUSTOMER_SERVICE:
            return ChatAgent()
        elif agent_type == AgentType.AUTOMATION:
            return FileAgent()
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
    except Exception as e:
        logger.error(f"Error creating agent of type {agent_type}: {e}")
        raise


class MultiAgentCodingAI:
    """Main orchestrator for the multi-agent system"""

    def __init__(self):
        """Initialize the multi-agent system."""
        self.agents = {}
        self.db = None
        self._initialize_database()
        self._initialize_agents()

    def _initialize_database(self):
        """Initialize database connection."""
        try:
            self.db = FirestoreClient()
            logger.info("Database connection initialized successfully")
        except Exception as e:
                logger.warning(f"Could not initialize database: {e}")
                self.db = None

    def _initialize_agents(self):
        """Initialize all available agents."""
        try:
            agent_types = [
                AgentType.CONTENT_CREATION,
                AgentType.DATA_ANALYSIS,
                AgentType.CUSTOMER_SERVICE,
                AgentType.AUTOMATION
            ]
            
            for agent_type in agent_types:
                try:
                    self.agents[agent_type] = create_agent(agent_type)
                    logger.info(f"Successfully initialized {agent_type.value} agent")
                except Exception as e:
                    logger.error(f"Failed to initialize {agent_type.value} agent: {e}")
                    
            if not self.agents:
                raise RuntimeError("No agents could be initialized")
                
            logger.info(f"Initialized {len(self.agents)} agents successfully")
            
        except Exception as e:
            logger.error(f"Error initializing agents: {e}")
            raise

    def route_request(
        self,
        request: str,
        agent_type: Optional[AgentType] = None,
        context: Optional[Dict] = None,
        session_id: Optional[str] = None
    ) -> AgentResponse:
        """Route request to appropriate agent or auto-detect"""
        start_time = time.time()
        session_id = session_id or str(uuid.uuid4())
        
        # Extract chat_history from context
        chat_history_from_context = context.get("chat_history", []) if context else []

        try:
            if not request or not request.strip():
                return AgentResponse(
                    content="Please provide a valid request.",
                    success=False,
                    error_message="Empty request provided",
                    execution_time=time.time() - start_time
                )
            
            if not agent_type:
                agent_type = self._detect_agent_type(request)

            logger.info(f"Routing request to {agent_type.value} agent")
            logger.info(f"Request: {request[:100]}...")

            if agent_type not in self.agents:
                logger.error(f"Agent {agent_type.value} not found in available agents")
                response = AgentResponse(
                    content="",
                    success=False,
                    agent_type=agent_type.value,
                    error_message=f"Agent {agent_type.value} is not available",
                    execution_time=time.time() - start_time
                )
                self._save_interaction(session_id, request, response, agent_type)
                return response

            # Pass chat_history to the agent's process method
            response = self.agents[agent_type].process(request, chat_history_from_context) 
            response.agent_type = agent_type.value
            response.execution_time = time.time() - start_time

            self._save_interaction(session_id, request, response, agent_type)

            logger.info(f"Response generated successfully. Content length: {len(response.content) if response.content else 0}")
            return response

        except Exception as e:
            logger.error(f"Error in route_request: {e}", exc_info=True)
            response = AgentResponse(
                content="",
                success=False,
                error_message=f"Routing error: {str(e)}",
                execution_time=time.time() - start_time
            )
            if agent_type:
                response.agent_type = agent_type.value
            self._save_interaction(session_id, request, response, agent_type)
            return response

    def _save_interaction(
        self,
        session_id: str,
        request: str,
        response: AgentResponse,
        agent_type: Optional[AgentType]
    ) -> None:
        """Save interaction to database."""
        try:
            if not self.db:
                logger.debug("Database not available, skipping interaction save")
                return
                
            response_dict = {
                'content': response.content or "",
                'success': response.success,
                'agent_type': response.agent_type or (agent_type.value if agent_type else "unknown"),
                'execution_time': response.execution_time,
                'error': response.error_message or response.error or ""
            }
            
            metadata = {
                'request_length': len(request),
                'response_length': len(response.content) if response.content else 0,
                'timestamp': time.time()
            }
            
            self.db.save_chat_history(
                session_id=session_id,
                request=request,
                response=response_dict,
                agent_type=response.agent_type or (agent_type.value if agent_type else "unknown"),
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Error saving interaction to database: {e}")

    def get_chat_history(
        self,
        session_id: str,
        limit: int = 50,
        start_after: Optional[str] = None
    ) -> List[Dict]:
        """Get chat history for a session."""
        try:
            if not self.db:
                logger.warning("Database not available")
                return []
            return self.db.get_chat_history(session_id, limit, start_after)
        except Exception as e:
            logger.error(f"Error retrieving chat history: {e}")
            return []

    def get_agent_stats(
        self,
        agent_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get statistics for agents."""
        try:
            if not self.db:
                logger.warning("Database not available")
                return {}
                
            if agent_type:
                return self.db.get_agent_stats(agent_type, start_date, end_date)
            else:
                stats = {}
                for agent in self.agents.values():
                    agent_stats = self.db.get_agent_stats(
                        agent.agent_type.value,
                        start_date,
                        end_date
                    )
                    stats[agent.agent_type.value] = agent_stats
                return stats
        except Exception as e:
            logger.error(f"Error getting agent stats: {e}")
            return {}

    def get_active_sessions(
        self,
        agent_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get list of active chat sessions."""
        try:
            if not self.db:
                logger.warning("Database not available")
                return []
            return self.db.get_active_sessions(agent_type, limit)
        except Exception as e:
            logger.error(f"Error getting active sessions: {e}")
            return []

    def _detect_agent_type(self, request: str) -> AgentType:
        """Auto-detect which agent should handle the request"""
        request_lower = request.lower().strip()

        # Check for simple acknowledgments first
        acknowledgment_phrases = [
            "thank you", "thanks", "appreciate it", "ok", "okay", "got it",
            "understood", "perfect", "great", "awesome", "nice", "good",
            "bye", "goodbye", "see you", "later", "end", "stop"
        ]
        
        if any(phrase in request_lower for phrase in acknowledgment_phrases):
            logger.info(f"Detected acknowledgment: {request}")
            return AgentType.CUSTOMER_SERVICE

        # Enhanced keywords for each agent type
        analysis_keywords = [
            "analyze", "data", "report", "chart", "sql", "query", "insights", 
            "metrics", "statistics", "dashboard", "visualization", "trend",
            "calculate", "compute", "process data"
        ]
        chat_keywords = [
            "help", "support", "issue", "problem", "question", "customer",
            "service", "chat", "talk", "discuss", "explain", "how to",
            "what is", "can you", "please help"
        ]
        file_keywords = [
            "file", "process", "schedule", "trigger", "pipeline", "automate",
            "workflow", "batch", "upload", "download", "automation",
            "script", "task"
        ]
        content_keywords = [
            "write", "create content", "generate", "draft", "blog post",
            "email", "social media", "article", "content", "copy",
            "marketing", "product description", "newsletter"
        ]

        # Count keyword matches
        scores = {
            AgentType.DATA_ANALYSIS: sum(1 for word in analysis_keywords if word in request_lower),
            AgentType.CUSTOMER_SERVICE: sum(1 for word in chat_keywords if word in request_lower),
            AgentType.AUTOMATION: sum(1 for word in file_keywords if word in request_lower),
            AgentType.CONTENT_CREATION: sum(1 for word in content_keywords if word in request_lower),
        }

        # Return agent type with highest score, default to CUSTOMER_SERVICE for general queries
        max_score_agent = max(scores.items(), key=lambda x: x[1])
        detected_type = max_score_agent[0] if max_score_agent[1] > 0 else AgentType.CUSTOMER_SERVICE
        
        logger.info(f"Detected agent type: {detected_type.value} (score: {max_score_agent[1]})")
        return detected_type

    def get_available_agents(self) -> List[str]:
        """Get list of available agent types."""
        return [agent_type.value for agent_type in self.agents.keys()]

    def health_check(self) -> Dict[str, Any]:
        """Perform health check on all agents."""
        health_status = {
            "system_status": "healthy",
            "agents": {},
            "database": "available" if self.db else "unavailable",
            "timestamp": datetime.now().isoformat()
        }
        
        for agent_type, agent in self.agents.items():
            try:
                # Simple test to check if agent is responsive
                test_response = agent.process("health check")
                health_status["agents"][agent_type.value] = {
                    "status": "healthy" if test_response.success else "unhealthy",
                    "model_initialized": agent.model is not None
                }
            except Exception as e:
                health_status["agents"][agent_type.value] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # Check if any agents are unhealthy
        unhealthy_agents = [
            agent for agent, status in health_status["agents"].items() 
            if status.get("status") != "healthy"
        ]
        
        if unhealthy_agents:
            health_status["system_status"] = "degraded"
            
        return health_status


# Backward compatibility - keep the old class name
class HackathonAgent(MultiAgentCodingAI):
    """Backward compatibility class"""
    pass