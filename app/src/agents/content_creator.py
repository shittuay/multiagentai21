from typing import Optional, Dict, Any
from .base import BaseAgent
from src.types import AgentResponse, AgentType
import os
import logging
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class ContentCreatorAgent(BaseAgent):
    """
    A versatile content creation agent capable of generating various types of content
    including but not limited to:
    - Blog posts
    - Social media posts
    - Articles
    - Marketing copy
    - Product descriptions
    - Email content
    - And more...
    """
    
    def __init__(self):
        super().__init__(AgentType.CONTENT_CREATION)
        self.name = "ContentCreatorAgent"
        self.description = "A versatile agent for generating various types of content"
        
        # Initialize content templates
        self.templates = {
            "blog_post": {
                "intro": "Engaging introduction that hooks the reader",
                "body": "Well-structured content with clear sections",
                "conclusion": "Strong conclusion with call to action",
                "format": "Professional, informative, and engaging"
            },
            "social_media": {
                "headline": "Attention-grabbing headline",
                "content": "Concise, engaging content",
                "hashtags": "Relevant hashtags for discoverability",
                "format": "Short, punchy, and shareable"
            },
            "article": {
                "title": "Clear, descriptive title",
                "introduction": "Compelling introduction",
                "main_content": "Detailed, well-researched content",
                "conclusion": "Summary and next steps",
                "format": "Informative, authoritative, and well-structured"
            }
        }

    def _initialize_model(self):
        """Initialize the AI model for content generation."""
        try:
            # Initialize Google PaLM API for content generation
            import google.generativeai as genai
            genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
            self.model = genai.GenerativeModel('gemini-1.5-pro')
        except Exception as e:
            logger.error(f"Error initializing PaLM model: {e}")
            # Fallback to a simple placeholder model
            self.model = None

    def _process_with_model(self, input_data: str) -> str:
        """Process input using the PaLM model."""
        if not self.model:
            return f"Generated content based on input: {input_data}"
        
        try:
            response = self.model.generate_content(input_data)
            return response.text if hasattr(response, 'text') else str(response)
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            return f"Generated content based on input: {input_data}"

    def process(self, input_data: str, session_id: Optional[str] = None) -> AgentResponse:
        """Process a content generation request and return appropriate content."""
        start_time = time.time()
        
        try:
            # Extract content requirements from the request
            content_requirements = self._analyze_request(input_data)
            
            # Generate content based on requirements
            content = self._generate_content(content_requirements)
            
            # Review and refine the content
            refined_content = self._review_and_refine(content, content_requirements)
            
            return AgentResponse(
                content=refined_content,
                success=True,
                agent_type=self.agent_type.value,
                execution_time=time.time() - start_time,
                metadata={
                    'input_length': len(input_data),
                    'output_length': len(refined_content),
                    'session_id': session_id,
                    'agent_name': self.name
                }
            )
            
        except Exception as e:
            logger.error(f"Error in ContentCreatorAgent.process: {e}", exc_info=True)
            return AgentResponse(
                content="",
                error=str(e),
                success=False,
                agent_type=self.agent_type.value,
                execution_time=time.time() - start_time,
                error_message=f"Content generation error: {str(e)}",
                metadata={
                    'input_length': len(input_data),
                    'session_id': session_id,
                    'agent_name': self.name
                }
            )

    def _analyze_request(self, request: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze the request to determine content requirements.
        
        Args:
            request (str): The original request
            context (Optional[Dict[str, Any]]): Additional context
            
        Returns:
            Dict[str, Any]: Structured content requirements
        """
        # Default requirements
        requirements = {
            "content_type": "general",  # Will be determined from request
            "target_audience": "general",
            "tone": "professional",
            "length": "medium",
            "keywords": [],
            "style_guide": {},
            "original_request": request  # Include the original user request
        }
        
        # Update requirements based on context if provided
        if context:
            requirements.update(context)
            
        # Improved content type detection with better intent recognition
        request_lower = request.lower()
        
        # Debug logging
        logger.info(f"Analyzing request: '{request}'")
        logger.info(f"Request lower: '{request_lower}'")
        
        # PRIORITY 1: Check for "how to" questions first (these are ALWAYS instructional, not content generation)
        # This check must come FIRST and override any content keywords
        if (request_lower.startswith("how to") or 
            "how do i" in request_lower or 
            "how can i" in request_lower or
            "how should i" in request_lower or
            "how would i" in request_lower):
            requirements["content_type"] = "instructional_guide"
            requirements["tone"] = "educational"
            requirements["target_audience"] = "learners"
            logger.info("Detected as instructional_guide (how to question)")
            return requirements  # Return immediately, don't check other conditions
        
        # PRIORITY 2: Check for specific content generation requests
        elif "write a blog" in request_lower or "create a blog" in request_lower:
            requirements["content_type"] = "blog_post"
            logger.info("Detected as blog_post (write/create)")
        elif "write a social media" in request_lower or "create a social media" in request_lower:
            requirements["content_type"] = "social_media"
            logger.info("Detected as social_media")
        elif "write an article" in request_lower or "create an article" in request_lower:
            requirements["content_type"] = "article"
            logger.info("Detected as article")
        elif "write marketing" in request_lower or "create marketing" in request_lower:
            requirements["content_type"] = "marketing_copy"
            logger.info("Detected as marketing_copy")
        elif "write product description" in request_lower or "create product description" in request_lower:
            requirements["content_type"] = "product_description"
            logger.info("Detected as product_description")
        elif "write email" in request_lower or "create email" in request_lower:
            requirements["content_type"] = "email_content"
            logger.info("Detected as email_content")
        # PRIORITY 3: Check for general content type keywords
        elif "blog" in request_lower and "post" in request_lower:
            requirements["content_type"] = "blog_post"
            logger.info("Detected as blog_post (keywords)")
        elif "social media" in request_lower or "tweet" in request_lower or "instagram" in request_lower:
            requirements["content_type"] = "social_media"
            logger.info("Detected as social_media (keywords)")
        elif "article" in request_lower:
            requirements["content_type"] = "article"
            logger.info("Detected as article (keywords)")
        elif "marketing" in request_lower or "copy" in request_lower:
            requirements["content_type"] = "marketing_copy"
            logger.info("Detected as marketing_copy (keywords)")
        elif "product" in request_lower and "description" in request_lower:
            requirements["content_type"] = "product_description"
            logger.info("Detected as product_description (keywords)")
        elif "email" in request_lower:
            requirements["content_type"] = "email_content"
            logger.info("Detected as email_content (keywords)")
        else:
            logger.info("No specific content type detected, using general")
        
        logger.info(f"Final content type: {requirements['content_type']}")
        return requirements
    
    def _generate_content(self, requirements: Dict[str, Any]) -> str:
        """
        Generate content based on the requirements.
        
        Args:
            requirements (Dict[str, Any]): Content requirements
            
        Returns:
            str: Generated content
        """
        content_type = requirements.get("content_type", "general")
        target_audience = requirements.get("target_audience", "general")
        tone = requirements.get("tone", "professional")
        keywords = requirements.get("keywords", [])
        
        # Get the original user request from the requirements
        original_request = requirements.get("original_request", "")
        
        # Debug logging
        logger.info(f"Generating content for type: {content_type}")
        logger.info(f"Original request: {original_request}")
        
        # Handle instructional guides differently
        if content_type == "instructional_guide":
            prompt = f"""User Question: {original_request}

Please provide a comprehensive, step-by-step guide that teaches the user how to accomplish what they're asking about.

Requirements:
- Provide clear, actionable steps
- Include best practices and tips
- Explain the reasoning behind each step
- Use an educational and helpful tone
- Make it easy to follow for beginners
- Include common mistakes to avoid
- Provide examples where helpful

Please structure your response as a clear instructional guide that directly answers the user's "how to" question."""
            logger.info("Using instructional guide prompt")
        else:
            # Create a detailed prompt for content generation
            prompt = f"""User Request: {original_request}

Please provide a comprehensive response to the user's request above.

Content Requirements:
- Content type: {content_type}
- Target audience: {target_audience}
- Tone: {tone}
- Keywords to include: {', '.join(keywords) if keywords else 'None specified'}

Please create engaging, well-structured content that directly addresses the user's question or request."""
            logger.info("Using content generation prompt")

        logger.info(f"Generated prompt: {prompt[:200]}...")
        return self._process_with_model(prompt)
    
    def _review_and_refine(self, content: str, requirements: Dict[str, Any]) -> str:
        """
        Review and refine the generated content.
        
        Args:
            content (str): The generated content
            requirements (Dict[str, Any]): Original requirements
            
        Returns:
            str: Refined content
        """
        # For now, return the content as is
        # TODO: Implement content review and refinement
        return content 