#!/usr/bin/env python3
"""
MultiAgentAI21 Setup Verification Script
Run this script to verify your Firebase and environment setup
"""

import os
import json
import sys
from pathlib import Path

def check_environment_variables():
    """Check if all required environment variables are set"""
    print("🔍 Checking Environment Variables...")
    
    required_vars = {
        'GOOGLE_APPLICATION_CREDENTIALS': 'Path to Firebase Admin SDK service account key',
        'GOOGLE_API_KEY': 'Google API key for Gemini',
    }
    
    optional_vars = {
        'FIREBASE_PROJECT_ID': 'Firebase project ID',
        'FIREBASE_API_KEY': 'Firebase API key',
        'FIREBASE_AUTH_DOMAIN': 'Firebase auth domain',
        'GOOGLE_CLOUD_PROJECT': 'Google Cloud project ID'
    }
    
    issues = []
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {description}")
            if var == 'GOOGLE_APPLICATION_CREDENTIALS':
                if os.path.exists(value):
                    print(f"   📁 File exists: {value}")
                else:
                    print(f"   ❌ File NOT found: {value}")
                    issues.append(f"Service account key file not found at {value}")
        else:
            print(f"❌ {var}: NOT SET - {description}")
            issues.append(f"{var} not set")
    
    for var, description in optional_vars.items():
        value = os.getenv(var)
        status = "✅" if value else "⚠️"
        print(f"{status} {var}: {description} {'(SET)' if value else '(NOT SET)'}")
    
    return issues

def check_firebase_admin_sdk():
    """Test Firebase Admin SDK initialization"""
    print("\n🔥 Testing Firebase Admin SDK...")
    
    try:
        import firebase_admin
        from firebase_admin import credentials, auth
        from firebase_admin.exceptions import FirebaseError
        
        # Check if already initialized
        try:
            app = firebase_admin.get_app()
            print("✅ Firebase Admin SDK already initialized")
        except ValueError:
            # Not initialized, try to initialize
            cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            if not cred_path:
                print("❌ Cannot initialize - GOOGLE_APPLICATION_CREDENTIALS not set")
                return False
                
            if not os.path.exists(cred_path):
                print(f"❌ Cannot initialize - Service account key not found: {cred_path}")
                return False
            
            try:
                cred = credentials.Certificate(cred_path)
                app = firebase_admin.initialize_app(cred)
                print("✅ Firebase Admin SDK initialized successfully")
            except Exception as e:
                print(f"❌ Failed to initialize Firebase Admin SDK: {e}")
                return False
        
        # Test basic functionality
        try:
            users_page = auth.list_users(max_results=1)
            print("✅ Firebase Admin SDK working - can list users")
            return True
        except Exception as e:
            print(f"❌ Firebase Admin SDK authentication failed: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ Cannot import Firebase Admin SDK: {e}")
        return False

def check_firestore_client():
    """Test Firestore client initialization"""
    print("\n📊 Testing Firestore Client...")
    
    try:
        from google.cloud import firestore
        import google.auth
        
        # Try to get default credentials
        try:
            credentials, project = google.auth.default()
            print(f"✅ Default credentials found for project: {project}")
        except Exception as e:
            print(f"❌ Cannot get default credentials: {e}")
            return False
        
        # Try to initialize Firestore client
        try:
            db = firestore.Client()
            print("✅ Firestore client initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Firestore client: {e}")
            return False
            
        # Test basic operation
        try:
            # Try to access a test collection (this should work even with restrictive rules)
            test_ref = db.collection('test').document('test')
            # Note: We won't actually write, just test the reference creation
            print("✅ Firestore client working - can create document references")
            return True
        except Exception as e:
            print(f"❌ Firestore client test failed: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ Cannot import Firestore client: {e}")
        return False

def check_project_structure():
    """Check if the project structure is correct"""
    print("\n📁 Checking Project Structure...")
    
    current_dir = Path.cwd()
    required_files = [
        'app.py',
        'src/auth_manager.py',
        'src/data_analysis.py',
        'src/automation_agent.py',
        'src/enhanced_content_creator.py'
    ]
    
    issues = []
    
    for file_path in required_files:
        full_path = current_dir / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - NOT FOUND")
            issues.append(f"Missing file: {file_path}")
    
    # Check for __init__.py files
    init_files = [
        'src/__init__.py'
    ]
    
    for init_file in init_files:
        full_path = current_dir / init_file
        if full_path.exists():
            print(f"✅ {init_file}")
        else:
            print(f"⚠️ {init_file} - NOT FOUND (may cause import issues)")
    
    return issues

def check_dependencies():
    """Check if required Python packages are installed"""
    print("\n📦 Checking Dependencies...")
    
    required_packages = [
        'streamlit',
        'firebase_admin',
        'google-cloud-firestore',
        'google-generativeai',
        'pandas',
        'plotly',
        'python-dotenv'
    ]
    
    issues = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - NOT INSTALLED")
            issues.append(f"Missing package: {package}")
    
    return issues

def test_firestore_rules():
    """Test if Firestore rules are working correctly"""
    print("\n🔒 Testing Firestore Rules...")
    
    app_id = "1:711067427943:web:3d4dfebf9c5f4e6b07a0c2"  # Your app ID from the rules
    
    print(f"📋 Your Firestore rules are configured for app ID: {app_id}")
    print("📋 Rules path: /artifacts/{app_id}/users/{userId}/chat_histories/{document}")
    print("📋 Authentication required: Yes (request.auth.uid == userId)")
    
    # We can't actually test the rules without authentication, but we can verify the structure
    print("⚠️ To test rules, you need to:")
    print("   1. Create a user account in your app")
    print("   2. Try to save/load chat history")
    print("   3. Check Firebase Console > Firestore > Usage tab for errors")

def main():
    """Run all verification checks"""
    print("🚀 MultiAgentAI21 Setup Verification")
    print("=" * 50)
    
    all_issues = []
    
    # Run all checks
    all_issues.extend(check_environment_variables())
    
    project_issues = check_project_structure()
    all_issues.extend(project_issues)
    
    dependency_issues = check_dependencies()
    all_issues.extend(dependency_issues)
    
    # Only test Firebase if basic setup is okay
    if not all_issues:
        firebase_ok = check_firebase_admin_sdk()
        firestore_ok = check_firestore_client()
        test_firestore_rules()
    else:
        print("\n⚠️ Skipping Firebase tests due to setup issues")
        firebase_ok = False
        firestore_ok = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 VERIFICATION SUMMARY")
    print("=" * 50)
    
    if all_issues:
        print("❌ Issues found:")
        for issue in all_issues:
            print(f"   • {issue}")
    else:
        print("✅ Basic setup looks good!")
    
    if not all_issues and firebase_ok and firestore_ok:
        print("✅ Firebase and Firestore are working!")
        print("\n🎯 Next steps:")
        print("   1. Run your Streamlit app: streamlit run app.py")
        print("   2. Create a test user account")
        print("   3. Test the chat functionality")
    else:
        print("\n🔧 Fix the issues above and run this script again")
    
    print("\n💡 If you're still having issues:")
    print("   • Check Firebase Console for detailed error messages")
    print("   • Enable debug logging in your app")
    print("   • Verify your Firestore rules in the Firebase Console")

if __name__ == "__main__":
    main()