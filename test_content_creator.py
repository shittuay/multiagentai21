from src.agent_core import MultiAgentCodingAI, AgentType
import asyncio
from typing import Dict, Any

def test_content_creation():
    """Test basic content creation without context."""
    # Initialize the agent system
    agent_system = MultiAgentCodingAI()
    
    # Test different content types
    test_requests = [
        "Write a blog post about how to be successful on TikTok",
        "Create a social media post about the latest AI trends",
        "Write an article about content creation strategies"
    ]
    
    print("Testing Basic Content Creation...\n")
    
    for request in test_requests:
        print(f"\n{'='*50}")
        print(f"Request: {request}")
        print(f"{'='*50}\n")
        
        response = agent_system.route_request(request, AgentType.CONTENT_CREATION)
        
        if response.success:
            print("Content Generated Successfully:")
            print(f"\n{response.content}\n")
            print(f"Execution time: {response.execution_time:.2f} seconds")
        else:
            print(f"Error: {response.error_message or response.error}")
        
        print("\n" + "-"*50 + "\n")

def test_enhanced_content_creation():
    """Test content creation with context and different content types."""
    # Initialize the agent system
    agent_system = MultiAgentCodingAI()
    
    # Test cases with context
    test_cases = [
        {
            "request": "Create marketing copy for our new AI-powered productivity app",
            "context": {
                "content_type": "marketing_copy",
                "target_audience": "busy professionals",
                "tone": "enthusiastic",
                "keywords": ["productivity", "AI", "automation", "efficiency"],
                "style_guide": {
                    "brand_voice": "professional yet approachable",
                    "avoid_terms": ["complex", "difficult", "hard to use"]
                }
            }
        },
        {
            "request": "Write a product description for our cloud storage solution",
            "context": {
                "content_type": "product_description",
                "target_audience": "enterprise IT managers",
                "tone": "technical but clear",
                "keywords": ["cloud storage", "security", "scalability", "enterprise"],
                "style_guide": {
                    "focus": "security and reliability",
                    "format": "bullet points for features"
                }
            }
        },
        {
            "request": "Draft an email to announce our new feature release",
            "context": {
                "content_type": "email_content",
                "target_audience": "existing customers",
                "tone": "excited and grateful",
                "keywords": ["new feature", "update", "improvement"],
                "style_guide": {
                    "length": "concise",
                    "include": ["benefits", "next steps"]
                }
            }
        }
    ]
    
    print("\nTesting Enhanced Content Creation with Context...\n")
    
    for test_case in test_cases:
        request = test_case["request"]
        context = test_case["context"]
        
        print(f"\n{'='*50}")
        print(f"Request: {request}")
        print(f"Context: {context}")
        print(f"{'='*50}\n")
        
        response = agent_system.route_request(
            request=request,
            agent_type=AgentType.CONTENT_CREATION,
            context=context
        )
        
        if response.success:
            print("Content Generated Successfully:")
            print(f"\n{response.content}\n")
            print(f"Execution time: {response.execution_time:.2f} seconds")
            
            # Verify context was applied
            print("\nContext Verification:")
            for key, value in context.items():
                if key == "keywords":
                    # Check if keywords are present in content
                    found_keywords = [kw for kw in value if kw.lower() in response.content.lower()]
                    print(f"Keywords found: {found_keywords}")
                elif key == "tone":
                    # Basic tone check (could be enhanced with sentiment analysis)
                    print(f"Tone specified: {value}")
        else:
            print(f"Error: {response.error_message or response.error}")
        
        print("\n" + "-"*50 + "\n")

def test_error_handling():
    """Test error handling and edge cases."""
    agent_system = MultiAgentCodingAI()
    
    test_cases = [
        {
            "request": "",  # Empty request
            "context": None,
            "expected_error": "Please provide a valid input"
        },
        {
            "request": "Generate content",  # Too vague
            "context": {
                "content_type": "invalid_type"  # Invalid content type
            },
            "expected_error": None  # Should handle gracefully
        },
        {
            "request": "Write a blog post",
            "context": {
                "content_type": "blog_post",
                "tone": "invalid_tone"  # Invalid tone
            },
            "expected_error": None  # Should handle gracefully
        }
    ]
    
    print("\nTesting Error Handling...\n")
    
    for test_case in test_cases:
        request = test_case["request"]
        context = test_case["context"]
        expected_error = test_case["expected_error"]
        
        print(f"\n{'='*50}")
        print(f"Request: {request}")
        print(f"Context: {context}")
        print(f"Expected Error: {expected_error}")
        print(f"{'='*50}\n")
        
        response = agent_system.route_request(
            request=request,
            agent_type=AgentType.CONTENT_CREATION,
            context=context
        )
        
        if response.success:
            print("Content Generated Successfully:")
            print(f"\n{response.content}\n")
        else:
            print(f"Error: {response.error_message or response.error}")
            if expected_error and expected_error in (response.error_message or response.error or ""):
                print("✓ Expected error received")
            else:
                print("✗ Unexpected error or no error received")
        
        print("\n" + "-"*50 + "\n")

if __name__ == "__main__":
    # Run all tests
    print("Starting Content Creator Agent Tests...\n")
    
    # Test basic content creation
    test_content_creation()
    
    # Test enhanced features
    test_enhanced_content_creation()
    
    # Test error handling
    test_error_handling()
    
    print("\nAll tests completed!") 