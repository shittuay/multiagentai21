# from src.agent_core import MultiAgentCodingAI, AgentType

# def test_thank_you_responses():
#     """Tests that thank you messages are handled appropriately."""
#     ai = MultiAgentCodingAI()
    
#     # Test different thank you variations
#     test_messages = [
#         "thank you",
#         "thanks",
#         "thank you so much",
#         "ok",
#         "okay",
#         "got it",
#         "perfect",
#         "great",
#         "awesome"
#     ]
    
#     for message in test_messages:
#         print(f"\n{'='*50}")
#         print(f"Testing: '{message}'")
#         print(f"{'='*50}")
        
#         response = ai.route_request(message)
        
#         if response.success:
#             print(f"✅ Agent: {response.agent_type}")
#             print(f"✅ Response: {response.content}")
#             print(f"✅ Execution Time: {response.execution_time:.2f} seconds")
#         else:
#             print(f"❌ Error: {response.error_message or response.error}")
#             print(f"❌ Execution Time: {response.execution_time:.2f} seconds")

# if __name__ == "__main__":
#     test_thank_you_responses() 

test_requests = [
    "PERFORM CALCULATIONS ONLY - NO OVERVIEW: GROUP BY company_size, show COUNT and MEAN of salary_usd",
    "group by store and calculate total sales", 
    "GROUP BY company_name and show count, sort by count descending, top 5"
]

for request in test_requests:
    print(f"\n🧪 Testing: {request}")
    response = agent.process(request)
    print(f"Success: {response.success}")
    print(f"Response: {response.content[:200]}...")