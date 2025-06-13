"""Test script for chat functionality with Firestore integration."""

import os
import sys
import logging
from datetime import datetime
import pytest
from dotenv import load_dotenv

# Add src directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent_core import MultiAgentCodingAI, AgentType
from src.api.firestore import FirestoreClient
from src.config.settings import validate_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_chat_session():
    """Test a complete chat session with database integration."""
    # Validate settings
    assert validate_settings(), "Missing required settings"
    
    # Initialize the multi-agent system
    ai = MultiAgentCodingAI()
    
    # Create a test session
    session_id = f"test_session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    logger.info(f"Starting test session: {session_id}")
    
    # Test messages
    test_messages = [
        "Write a blog post about how to be successful on TikTok",
        "Create a social media post about the latest AI trends",
        "Write an article about content creation strategies"
    ]
    
    # Process each message
    for message in test_messages:
        logger.info(f"\nProcessing message: {message}")
        
        # Get response from agent
        response = ai.route_request(
            request=message,
            session_id=session_id
        )
        
        # Print response
        print("\n" + "="*50)
        print(f"Request: {message}")
        print("="*50)
        print(f"Response: {response.content}")
        print(f"Success: {response.success}")
        print(f"Execution time: {response.execution_time:.2f} seconds")
        if not response.success:
            print(f"Error: {response.error_message}")
        print("="*50 + "\n")
        
        # Verify response was saved to database
        db = FirestoreClient()
        history = db.get_chat_history(session_id, limit=1)
        assert len(history) > 0, "Chat history not saved to database"
        assert history[0]['request'] == message, "Saved request doesn't match"
        assert history[0]['response']['content'] == response.content, "Saved response doesn't match"
    
    # Get session statistics
    stats = ai.get_agent_stats()
    print("\nAgent Statistics:")
    print("="*50)
    for agent_type, agent_stats in stats.items():
        print(f"\n{agent_type}:")
        print(f"Total requests: {agent_stats['total_requests']}")
        print(f"Successful requests: {agent_stats['successful_requests']}")
        print(f"Failed requests: {agent_stats['failed_requests']}")
        print(f"Average response time: {agent_stats['average_response_time']:.2f} seconds")
    
    # Get active sessions
    active_sessions = ai.get_active_sessions()
    print("\nActive Sessions:")
    print("="*50)
    for session in active_sessions:
        print(f"Session ID: {session.get('session_id', 'N/A')}")
        print(f"Agent Type: {session.get('agent_type', 'N/A')}")
        print(f"Last Interaction: {session.get('last_interaction', 'N/A')}")
        print("-"*30)

if __name__ == "__main__":
    test_chat_session() 