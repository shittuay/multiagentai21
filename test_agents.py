#!/usr/bin/env python3
"""
Test script for MultiAgentAI21 agents
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src.agent_core import MultiAgentCodingAI, AgentType

def test_agents():
    """Test all agents with sample requests."""
    
    print("🚀 Testing MultiAgentAI21 Agents")
    print("=" * 50)
    
    # Initialize the agent system
    try:
        agent_system = MultiAgentCodingAI()
        print("✅ Agent system initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize agent system: {e}")
        return
    
    # Test cases for each agent
    test_cases = [
        {
            "agent": AgentType.CONTENT_CREATION,
            "request": "Write a blog post about the benefits of remote work",
            "description": "Content Creation Agent"
        },
        {
            "agent": AgentType.DATA_ANALYSIS,
            "request": "How can I analyze employee salary data to identify pay disparities?",
            "description": "Data Analysis Agent"
        },
        {
            "agent": AgentType.CUSTOMER_SERVICE,
            "request": "A customer is complaining about a late delivery, how should I handle this?",
            "description": "Customer Service Agent"
        },
        {
            "agent": AgentType.AUTOMATION,
            "request": "How can I automate the process of sending weekly reports to clients?",
            "description": "Automation Agent"
        }
    ]
    
    # Run tests
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['description']}")
        print(f"📝 Request: {test_case['request']}")
        print("-" * 40)
        
        try:
            response = agent_system.route_request(
                test_case['request'],
                test_case['agent']
            )
            
            if response and response.success:
                print(f"✅ Success! Response length: {len(response.content)} characters")
                print(f"⏱️ Execution time: {response.execution_time:.2f}s")
                print(f"📄 Response preview: {response.content[:200]}...")
            else:
                print(f"❌ Failed: {response.error_message if response else 'No response'}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 40)
    
    print("\n🎯 Testing completed!")

if __name__ == "__main__":
    test_agents() 