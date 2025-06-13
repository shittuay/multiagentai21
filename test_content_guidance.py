from src.agent_core import MultiAgentCodingAI, AgentType

def test_content_guidance():
    """Tests the Content Creation Agent for guidance generation."""
    ai = MultiAgentCodingAI()
    
    # Test for guidance on how to create a blog post
    request = "HOW TO CREATE A BLOG POST"
    print(f"Testing guidance request: \"{request}\"")
    response = ai.route_request(request, agent_type=AgentType.CONTENT_CREATION)
    
    if response.success:
        print("\n--- Agent Response (Success) ---")
        print(response.content)
        print(f"Execution Time: {response.execution_time:.2f} seconds")
    else:
        print("\n--- Agent Response (Failure) ---")
        print(f"Error: {response.error_message or response.error}")
        print(f"Execution Time: {response.execution_time:.2f} seconds")

if __name__ == "__main__":
    test_content_guidance() 