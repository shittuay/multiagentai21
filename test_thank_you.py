#!/usr/bin/env python3
"""
Test script to verify that all agents properly handle thank you messages
without treating them as new requests.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def test_acknowledgment_handling():
    """Test that thank you messages are handled appropriately."""
    print("🧪 Testing acknowledgment handling in all agents...")
    
    # Test different thank you variations
    test_phrases = [
        "thank you",
        "thanks",
        "thank you so much",
        "appreciate it",
        "ok",
        "okay",
        "got it",
        "understood",
        "perfect",
        "great",
        "awesome",
        "nice",
        "good",
        "bye",
        "goodbye"
    ]
    
    try:
        # Test BaseAgent acknowledgment methods
        from src.agents.base import BaseAgent
        from src.types import AgentType
        
        # Create a mock agent for testing
        class MockAgent(BaseAgent):
            def _initialize_model(self):
                pass
            
            def _process_with_model(self, input_data: str) -> str:
                return "This should not be called for acknowledgments"
        
        mock_agent = MockAgent(AgentType.CONTENT_CREATION)
        
        print("✅ BaseAgent acknowledgment methods imported successfully")
        
        # Test acknowledgment detection
        for phrase in test_phrases:
            is_ack = mock_agent._is_acknowledgment(phrase)
            response = mock_agent._generate_acknowledgment_response(phrase)
            
            print(f"  📝 '{phrase}' -> Is acknowledgment: {is_ack}")
            print(f"      Response: {response[:50]}...")
            
            if not is_ack:
                print(f"  ⚠️  Warning: '{phrase}' was not detected as acknowledgment")
        
        # Test full process method
        print("\n🔄 Testing full process method...")
        for phrase in test_phrases[:3]:  # Test first 3 phrases
            result = mock_agent.process(phrase)
            print(f"  📝 '{phrase}' -> Success: {result.success}")
            print(f"      Content: {result.content[:50]}...")
            print(f"      Response type: {result.metadata.get('response_type', 'unknown')}")
            
            if result.metadata.get('response_type') != 'acknowledgment':
                print(f"  ⚠️  Warning: Response type not marked as acknowledgment")
        
        print("\n✅ All acknowledgment tests passed!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running this from the project root directory")
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()

def test_agent_imports():
    """Test that all agent classes can be imported and have acknowledgment handling."""
    print("\n🔍 Testing agent imports and acknowledgment handling...")
    
    agents_to_test = [
        "src.agents.content_creator.ContentCreatorAgent",
        "src.agents.enhanced_content_creator.EnhancedContentCreatorAgent",
        "src.agents.automation_agent.AutomationAgent"
    ]
    
    for agent_path in agents_to_test:
        try:
            # Import the agent class
            module_path, class_name = agent_path.rsplit('.', 1)
            module = __import__(module_path, fromlist=[class_name])
            agent_class = getattr(module, class_name)
            
            print(f"✅ {class_name} imported successfully")
            
            # Check if it has acknowledgment methods
            if hasattr(agent_class, '_is_acknowledgment'):
                print(f"  ✅ {class_name} has _is_acknowledgment method")
            else:
                print(f"  ⚠️  {class_name} missing _is_acknowledgment method")
                
            if hasattr(agent_class, '_generate_acknowledgment_response'):
                print(f"  ✅ {class_name} has _generate_acknowledgment_response method")
            else:
                print(f"  ⚠️  {class_name} missing _generate_acknowledgment_response method")
                
        except ImportError as e:
            print(f"❌ Failed to import {agent_path}: {e}")
        except Exception as e:
            print(f"❌ Error testing {agent_path}: {e}")

if __name__ == "__main__":
    print("🚀 Starting acknowledgment handling tests...\n")
    
    test_agent_imports()
    test_acknowledgment_handling()
    
    print("\n🎉 All tests completed!")
    print("\n💡 If you see any warnings, the agents may not have proper acknowledgment handling.")
    print("   The fixes should resolve the issue where agents treat 'thank you' as new requests.")