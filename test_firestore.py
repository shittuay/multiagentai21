#!/usr/bin/env python3
"""
Test script for Firestore connectivity and permissions
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

def test_firestore_connection():
    """Test Firestore connection and basic operations."""
    
    print("🔥 Testing Firestore Connection")
    print("=" * 50)
    
    # Check environment variables
    print("📋 Checking environment variables...")
    project_id = os.getenv('GOOGLE_PROJECT_ID')
    credentials_file = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    if not project_id:
        print("❌ GOOGLE_PROJECT_ID not set")
        return False
    
    if not credentials_file:
        print("❌ GOOGLE_APPLICATION_CREDENTIALS not set")
        return False
    
    if not os.path.exists(credentials_file):
        print(f"❌ Credentials file not found: {credentials_file}")
        return False
    
    print(f"✅ Project ID: {project_id}")
    print(f"✅ Credentials file: {credentials_file}")
    
    # Test Firestore connection
    try:
        print("\n🔌 Testing Firestore connection...")
        from google.cloud import firestore
        
        # Initialize client
        client = firestore.Client()
        print("✅ Firestore client initialized")
        
        # Test basic operations
        print("\n📝 Testing write operation...")
        test_collection = client.collection('test_connection')
        test_doc = test_collection.document('test_doc')
        
        test_data = {
            'timestamp': datetime.utcnow(),
            'message': 'Test connection successful',
            'project_id': project_id
        }
        
        test_doc.set(test_data)
        print("✅ Write operation successful")
        
        # Test read operation
        print("\n📖 Testing read operation...")
        doc_snapshot = test_doc.get()
        if doc_snapshot.exists:
            print("✅ Read operation successful")
            print(f"📄 Document data: {doc_snapshot.to_dict()}")
        else:
            print("❌ Read operation failed")
            return False
        
        # Test delete operation
        print("\n🗑️ Testing delete operation...")
        test_doc.delete()
        print("✅ Delete operation successful")
        
        # Test collections
        print("\n📚 Testing collections...")
        collections = list(client.collections())
        print(f"✅ Found {len(collections)} collections")
        
        return True
        
    except Exception as e:
        print(f"❌ Firestore connection failed: {e}")
        return False

def test_multiagentai21_firestore():
    """Test MultiAgentAI21 specific Firestore operations."""
    
    print("\n🤖 Testing MultiAgentAI21 Firestore Integration")
    print("=" * 50)
    
    try:
        from src.api.firestore import FirestoreClient
        
        # Initialize Firestore client
        firestore_client = FirestoreClient()
        
        if not firestore_client.initialized:
            print("❌ Firestore client not initialized")
            return False
        
        print("✅ Firestore client initialized")
        
        # Test chat history save
        print("\n💬 Testing chat history save...")
        session_id = f"test_session_{int(datetime.utcnow().timestamp())}"
        
        test_response = {
            'content': 'This is a test response',
            'success': True,
            'agent_type': 'test_agent',
            'execution_time': 1.5
        }
        
        doc_id = firestore_client.save_chat_history(
            session_id=session_id,
            request="Test request",
            response=test_response,
            agent_type="test_agent",
            metadata={'test': True}
        )
        
        if doc_id and doc_id != "error":
            print(f"✅ Chat history saved with ID: {doc_id}")
        else:
            print("❌ Chat history save failed")
            return False
        
        # Test chat history retrieval
        print("\n📖 Testing chat history retrieval...")
        chat_history = firestore_client.get_chat_history(session_id)
        
        if chat_history:
            print(f"✅ Retrieved {len(chat_history)} chat entries")
        else:
            print("❌ Chat history retrieval failed")
            return False
        
        # Test agent stats
        print("\n📊 Testing agent stats...")
        stats = firestore_client.get_agent_stats("test_agent")
        
        if stats:
            print("✅ Agent stats retrieved")
            print(f"📈 Stats: {stats}")
        else:
            print("❌ Agent stats retrieval failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ MultiAgentAI21 Firestore test failed: {e}")
        return False

def main():
    """Main test function."""
    
    print("🚀 Firestore Integration Test Suite")
    print("=" * 60)
    
    # Test basic connection
    connection_ok = test_firestore_connection()
    
    if connection_ok:
        # Test MultiAgentAI21 integration
        integration_ok = test_multiagentai21_firestore()
        
        if integration_ok:
            print("\n🎉 All tests passed! Firestore is properly configured.")
            print("\n✅ You can now run your MultiAgentAI21 application with full database functionality.")
        else:
            print("\n⚠️ Basic connection works, but MultiAgentAI21 integration has issues.")
            print("Check the Firestore setup guide for troubleshooting.")
    else:
        print("\n❌ Firestore connection failed. Please check your configuration.")
        print("Follow the FIRESTORE_SETUP.md guide to configure Firestore properly.")

if __name__ == "__main__":
    main() 