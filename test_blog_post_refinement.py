from src.agent_core import MultiAgentCodingAI, AgentType

def test_blog_post_refinement():
    """Tests the Content Creation Agent for refining an existing blog post."""
    ai = MultiAgentCodingAI()
    
    # The existing blog post content provided by the user
    existing_blog_post = """
Artificial intelligence (AI) is rapidly transforming modern society, permeating various aspects of our lives from the mundane to the extraordinary. Its influence is undeniable, presenting both remarkable opportunities and significant challenges that we must navigate thoughtfully.

One of the most visible impacts of AI is its automation of tasks. Repetitive and data-heavy processes, previously requiring human intervention, are now often handled by AI-powered systems. This boosts efficiency in industries like manufacturing, customer service, and finance, freeing up human workers to focus on more complex and creative endeavors. Furthermore, AI-driven automation can lead to increased productivity and reduced operational costs, making businesses more competitive and potentially leading to lower prices for consumers.

Beyond automation, AI is revolutionizing healthcare. AI-powered diagnostic tools can analyze medical images with greater speed and accuracy than humans, aiding in early disease detection and personalized treatment plans. AI is also being used to develop new drugs and therapies, accelerating the pace of medical innovation and offering hope for previously incurable diseases.

In the realm of communication and information access, AI is also playing a pivotal role. Natural language processing allows for more sophisticated and intuitive interactions with computers, enabling voice assistants, chatbots, and real-time translation services. Search engines utilize AI algorithms to provide more relevant and personalized search results, connecting users with information more efficiently than ever before.

However, the rise of AI also presents challenges. Job displacement due to automation is a valid concern that requires proactive solutions, including retraining programs and social safety nets. Ethical considerations surrounding AI decision-making, particularly in areas like criminal justice and loan applications, need careful examination to ensure fairness and prevent bias. Furthermore, the potential for misuse of AI, such as in the development of autonomous weapons or the spread of disinformation, requires international cooperation and robust regulatory frameworks.

The future of AI is inextricably linked to the future of humanity. By fostering responsible development and deployment of AI technologies, we can harness its immense potential for good while mitigating its risks. Open discussions, ongoing research, and collaborative efforts between governments, industry leaders, and researchers are crucial to ensuring that AI benefits all of society and contributes to a more prosperous and equitable future.
    """

    # Request to refine the blog post
    request = f"Refine and improve the following blog post on 'The Impact of Artificial Intelligence on Modern Society':\n\n{existing_blog_post}"
    print(f"Testing blog post refinement request: \"{request[:100]}...\"")
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
    test_blog_post_refinement() 