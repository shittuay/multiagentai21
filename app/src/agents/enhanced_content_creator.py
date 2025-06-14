from typing import Optional, Dict, Any
from src.agent_core import ContentCreatorAgent
from src.types import AgentResponse, AgentType
import logging
import json
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class EnhancedContentCreatorAgent(ContentCreatorAgent):
    """
    An enhanced version of the ContentCreatorAgent that adds:
    - More content types
    - Better context handling
    - Content review and refinement
    - Advanced request analysis
    """
    
    def __init__(self):
        """Initialize the enhanced content creator agent."""
        super().__init__()
        self.name = "EnhancedContentCreatorAgent"
        self.description = "An enhanced agent for generating various types of content"
        
        # Add new content types to templates
        self.templates.update({
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
        })

    def process(self, input_data: str, session_id: Optional[str] = None) -> AgentResponse:
        """Process a content generation request with enhanced context support."""
        start_time = time.time()
        
        try:
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

            # Check if this is a refinement request
            refinement_patterns = [
                "refine and improve",
                "improve this",
                "enhance this",
                "edit this",
                "revise this",
                "polish this",
                "make this better",
                "optimize this"
            ]
            
            is_refinement_request = any(pattern in input_lower for pattern in refinement_patterns)

            if is_guidance_request:
                logger.info(f"Detected guidance request: {input_data}")
                # Generate guidance content
                return self._generate_guidance_content(input_data, start_time)
            
            if is_refinement_request:
                logger.info(f"Detected refinement request: {input_data[:100]}...")
                # Generate refined content
                return self._generate_refined_content(input_data, start_time)

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
            logger.error(f"Error in EnhancedContentCreatorAgent.process: {e}", exc_info=True)
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
        """Analyze the request to determine content requirements."""
        # Default requirements
        requirements = {
            "content_type": "general",
            "target_audience": "general",
            "tone": "professional",
            "length": "medium",
            "keywords": [],
            "style_guide": {}
        }
        
        # Update requirements based on context if provided
        if context:
            requirements.update(context)
            
        # TODO: Implement more sophisticated request analysis
        # This could include:
        # - NLP to determine content type from request
        # - Sentiment analysis to determine tone
        # - Keyword extraction
        # - Length estimation
        
        return requirements

    def _generate_content(self, requirements: Dict[str, Any]) -> str:
        """Generate content based on the requirements."""
        content_type = requirements.get("content_type", "general")
        
        # Map content type to appropriate generation method
        generation_methods = {
            "blog_post": self._generate_blog_post,
            "social_media": self._generate_social_media_post,
            "article": self._generate_article,
            "marketing_copy": self._generate_marketing_copy,
            "product_description": self._generate_product_description,
            "email_content": self._generate_email_content,
            "general": self._generate_general_content
        }
        
        # Get the appropriate generation method
        generate_method = generation_methods.get(content_type, self._generate_general_content)
        
        # Create a prompt that includes all requirements
        prompt = self._create_prompt_from_requirements(requirements)
        
        # Generate the content
        return generate_method(prompt)

    def _create_prompt_from_requirements(self, requirements: Dict[str, Any]) -> str:
        """Create a detailed prompt from content requirements."""
        prompt_parts = [
            f"Content Type: {requirements.get('content_type', 'general')}",
            f"Target Audience: {requirements.get('target_audience', 'general')}",
            f"Tone: {requirements.get('tone', 'professional')}",
            f"Length: {requirements.get('length', 'medium')}",
        ]
        
        if requirements.get('keywords'):
            prompt_parts.append(f"Keywords to include: {', '.join(requirements['keywords'])}")
            
        if requirements.get('style_guide'):
            prompt_parts.append(f"Style Guide: {json.dumps(requirements['style_guide'])}")
            
        return "\n".join(prompt_parts)

    def _review_and_refine(self, content: str, requirements: Dict[str, Any]) -> str:
        """Review and refine the generated content."""
        # For now, return the content as is
        # TODO: Implement content review and refinement
        return content

    def _generate_marketing_copy(self, prompt: str) -> str:
        """Generate marketing copy using PaLM API."""
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

        return self._process_with_model(marketing_prompt)

    def _generate_product_description(self, prompt: str) -> str:
        """Generate product description using PaLM API."""
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

        return self._process_with_model(product_prompt)

    def _generate_email_content(self, prompt: str) -> str:
        """Generate email content using PaLM API."""
        email_prompt = f"""Create an effective email about: {prompt}

Follow these guidelines:
1. Write an attention-grabbing subject line
2. Use a personalized greeting
3. Keep the message clear and concise
4. Focus on a single main point
5. Use a professional but engaging tone
6. Include a clear call to action
7. End with a professional sign-off
8. Keep it mobile-friendly

Format the response with clear sections."""

        return self._process_with_model(email_prompt)

    def _generate_blog_post(self, prompt: str) -> str:
        """Generate blog post using PaLM API."""
        blog_prompt = f"""Write an engaging blog post about: {prompt}

Follow these guidelines:
1. Create a compelling headline
2. Write an engaging introduction
3. Structure content with clear sections
4. Use subheadings for readability
5. Include relevant examples or data
6. Write a strong conclusion
7. Add a call to action
8. Keep it informative and engaging

Format the response with clear sections and headings."""

        return self._process_with_model(blog_prompt)

    def _generate_social_media_post(self, prompt: str) -> str:
        """Generate social media post using PaLM API."""
        social_prompt = f"""Create an engaging social media post about: {prompt}

Follow these guidelines:
1. Write an attention-grabbing headline
2. Keep content concise and engaging
3. Use conversational tone
4. Include relevant hashtags
5. Add a call to action
6. Make it shareable
7. Use emojis appropriately
8. Keep it under 280 characters for Twitter

Format the response with clear sections."""

        return self._process_with_model(social_prompt)

    def _generate_article(self, prompt: str) -> str:
        """Generate article using PaLM API."""
        article_prompt = f"""Write a comprehensive article about: {prompt}

Follow these guidelines:
1. Create a clear, descriptive title
2. Write a compelling introduction
3. Structure with clear sections
4. Include relevant research or data
5. Use authoritative tone
6. Provide valuable insights
7. Write a strong conclusion
8. Include next steps or recommendations

Format the response with clear sections and headings."""

        return self._process_with_model(article_prompt)

    def _generate_general_content(self, prompt: str) -> str:
        """Generate general content using PaLM API."""
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

        return self._process_with_model(general_prompt)

    def _generate_guidance_content(self, prompt: str, start_time: float) -> AgentResponse:
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
        response_text = self._process_with_model(guidance_prompt)
        
        return AgentResponse(
            content=f"## 💡 Guidance on Content Creation\n\n{response_text}\n\n---\n*Guidance by MultiAgentAI21 Enhanced Content Creation Agent*",
            success=True,
            agent_type=self.agent_type.value,
            execution_time=time.time() - start_time,
            metadata={
                'input_length': len(prompt),
                'output_length': len(response_text),
                'agent_name': self.name,
                'guidance_request': True
            }
        )

    def _generate_refined_content(self, prompt: str, start_time: float) -> AgentResponse:
        """Generate refined and improved content based on existing content."""
        refinement_prompt = f"""
        You are an expert content editor and writer with extensive experience in improving and refining content.
        
        TASK: Refine and improve the following content to make it more engaging, clear, and effective.
        
        CONTENT TO REFINE: {prompt}
        
        Please provide an improved version that:
        
        1. **Enhances Clarity**: Makes the content easier to understand and follow
        2. **Improves Structure**: Better organization with clear headings and logical flow
        3. **Strengthens Arguments**: Adds supporting evidence, examples, or data where appropriate
        4. **Enhances Engagement**: Makes the content more compelling and interesting to read
        5. **Optimizes for SEO**: Includes relevant keywords naturally and improves readability
        6. **Polishes Language**: Fixes grammar, improves word choice, and enhances flow
        7. **Adds Value**: Provides additional insights or actionable takeaways
        8. **Maintains Original Message**: Preserves the core message and intent of the original content
        
        Format the response with:
        - Clear headings and subheadings
        - Proper paragraph breaks
        - Bullet points or numbered lists where appropriate
        - Bold text for emphasis on key points
        - A compelling introduction and strong conclusion
        
        Provide the refined content directly, not instructions on how to refine it.
        """
        
        response_text = self._process_with_model(refinement_prompt)
        
        return AgentResponse(
            content=f"## ✨ Refined Content\n\n{response_text}\n\n---\n*Refined by MultiAgentAI21 Enhanced Content Creation Agent*",
            success=True,
            agent_type=self.agent_type.value,
            execution_time=time.time() - start_time,
            metadata={
                'input_length': len(prompt),
                'output_length': len(response_text),
                'agent_name': self.name,
                'refinement_request': True
            }
        ) 