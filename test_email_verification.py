#!/usr/bin/env python3
"""
Test script to demonstrate email verification functionality
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def test_auth_manager_imports():
    """Test that the enhanced auth manager can be imported."""
    print("🔐 Testing Enhanced Authentication Manager...")
    
    try:
        from app.src.auth_manager import (
            initialize_firebase,
            create_user_account,
            authenticate_user,
            send_verification_email,
            verify_email_code,
            resend_verification_email,
            is_authenticated,
            get_current_user,
            logout,
            is_legacy_account,
            handle_legacy_user_login,
            initiate_signup,
            complete_signup_after_verification
        )
        
        print("✅ All authentication functions imported successfully")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_firebase_initialization():
    """Test Firebase initialization."""
    print("\n🔥 Testing Firebase Initialization...")
    
    try:
        from app.src.auth_manager import initialize_firebase
        
        firebase_available = initialize_firebase()
        
        if firebase_available:
            print("✅ Firebase Admin SDK initialized successfully")
            print("   - Email verification will use Firebase Authentication")
            print("   - Secure user management enabled")
        else:
            print("⚠️  Firebase not available")
            print("   - Using local authentication fallback")
            print("   - Limited security features")
        
        return firebase_available
        
    except Exception as e:
        print(f"❌ Firebase initialization error: {e}")
        return False

def test_legacy_account_detection():
    """Test legacy account detection functionality."""
    print("\n🕰️ Testing Legacy Account Detection...")
    
    try:
        from app.src.auth_manager import is_legacy_account
        from datetime import datetime
        
        # Test dates
        test_cases = [
            ("2024-11-15", True, "Account created before email verification"),
            ("2024-12-01", False, "Account created on email verification date"),
            ("2024-12-15", False, "Account created after email verification"),
            ("2023-06-01", True, "Old account from 2023"),
            ("2025-01-01", False, "Future account"),
            (None, True, "No creation date (assumed legacy)"),
        ]
        
        all_passed = True
        
        for date_str, expected, description in test_cases:
            if date_str:
                test_date = datetime.fromisoformat(date_str)
                result = is_legacy_account(test_date)
            else:
                result = is_legacy_account(None)
            
            status = "✅" if result == expected else "❌"
            print(f"   {status} {date_str or 'None'} -> {result} (Expected: {expected}) - {description}")
            
            if result != expected:
                all_passed = False
        
        if all_passed:
            print("✅ All legacy account detection tests passed!")
        else:
            print("❌ Some legacy account detection tests failed!")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error testing legacy account detection: {e}")
        return False

def test_new_signup_flow():
    """Test the new signup flow where verification email is sent immediately."""
    print("\n📝 Testing New Signup Flow (Verification First)...")
    
    try:
        from app.src.auth_manager import initiate_signup, complete_signup_after_verification
        
        # Test data
        test_email = "new_signup@example.com"
        test_password = "SecurePass123!"
        test_display_name = "New Signup User"
        
        print(f"Testing signup flow for: {test_email}")
        
        # Step 1: Initiate signup (sends verification email)
        print("1️⃣ Initiating signup...")
        success, verification_code, message = initiate_signup(
            email=test_email,
            password=test_password,
            display_name=test_display_name
        )
        
        if not success:
            print(f"❌ Signup initiation failed: {message}")
            return False
        
        print("✅ Signup initiated successfully!")
        print(f"   Verification code: {verification_code}")
        print(f"   Message: {message}")
        
        # Step 2: Complete signup after verification
        print("2️⃣ Completing signup after verification...")
        account_created, user_id, create_message = complete_signup_after_verification()
        
        if account_created:
            print("✅ Account created successfully!")
            print(f"   User ID: {user_id}")
            print(f"   Message: {create_message}")
            return True
        else:
            print(f"❌ Account creation failed: {create_message}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing new signup flow: {e}")
        return False

def test_user_account_creation():
    """Test user account creation with email verification."""
    print("\n📝 Testing User Account Creation...")
    
    try:
        from app.src.auth_manager import create_user_account
        
        # Test data
        test_email = "test@example.com"
        test_password = "SecurePass123!"
        test_display_name = "Test User"
        
        print(f"Creating account for: {test_email}")
        
        success, user_id, message = create_user_account(
            email=test_email,
            password=test_password,
            display_name=test_display_name
        )
        
        if success:
            print(f"✅ Account created successfully!")
            print(f"   User ID: {user_id}")
            print(f"   Message: {message}")
            return True, user_id
        else:
            print(f"❌ Account creation failed: {message}")
            return False, None
            
    except Exception as e:
        print(f"❌ Error testing account creation: {e}")
        return False, None

def test_email_verification():
    """Test email verification process."""
    print("\n📧 Testing Email Verification...")
    
    try:
        from app.src.auth_manager import send_verification_email, verify_email_code
        
        test_email = "verify@example.com"
        
        # Send verification email
        print(f"Sending verification email to: {test_email}")
        verification_sent, verification_code = send_verification_email(test_email, "test_code_123")
        
        if verification_sent:
            print("✅ Verification email sent successfully")
            print(f"   Verification code: {verification_code}")
            
            # Test verification
            print("Testing email verification...")
            success, message = verify_email_code(test_email, verification_code)
            
            if success:
                print("✅ Email verification successful!")
                print(f"   Message: {message}")
                return True
            else:
                print(f"❌ Email verification failed: {message}")
                return False
        else:
            print(f"❌ Failed to send verification email: {verification_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing email verification: {e}")
        return False

def test_legacy_user_authentication():
    """Test authentication for legacy users (existing accounts)."""
    print("\n👴 Testing Legacy User Authentication...")
    
    try:
        from app.src.auth_manager import authenticate_user, is_legacy_account
        from datetime import datetime, timedelta
        
        # Simulate a legacy user in local storage
        legacy_email = "legacy@example.com"
        legacy_password = "LegacyPass123!"
        
        # Create a mock legacy user in session state
        import streamlit as st
        
        # Clear any existing session data
        for key in ["local_users", "authenticated", "user_email", "user_uid", "user_name"]:
            if key in st.session_state:
                del st.session_state[key]
        
        # Create legacy user (created before email verification)
        legacy_creation_date = datetime.now() - timedelta(days=30)  # 30 days ago
        local_users = {
            legacy_email: {
                "uid": "legacy_user_123",
                "email": legacy_email,
                "display_name": "Legacy User",
                "password_hash": hash(legacy_password),
                "created_at": legacy_creation_date.isoformat(),
                "email_verified": False,
                "requires_verification": False
            }
        }
        st.session_state["local_users"] = local_users
        
        print(f"Created mock legacy user: {legacy_email}")
        print(f"   Creation date: {legacy_creation_date.strftime('%Y-%m-%d')}")
        print(f"   Is legacy: {is_legacy_account(legacy_creation_date)}")
        
        # Test authentication
        print("Testing legacy user authentication...")
        success, user_id, message = authenticate_user(legacy_email, legacy_password)
        
        if success:
            print("✅ Legacy user authentication successful!")
            print(f"   User ID: {user_id}")
            print(f"   Message: {message}")
            return True
        else:
            print(f"❌ Legacy user authentication failed: {message}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing legacy user authentication: {e}")
        return False

def test_authentication_flow():
    """Test the complete authentication flow."""
    print("\n🔄 Testing Complete Authentication Flow...")
    
    try:
        from app.src.auth_manager import (
            create_user_account,
            send_verification_email,
            verify_email_code,
            authenticate_user
        )
        
        # Step 1: Create account
        print("1️⃣ Creating test account...")
        success, user_id = create_user_account(
            email="auth_test@example.com",
            password="SecurePass123!",
            display_name="Auth Test User"
        )
        
        if not success:
            print("❌ Account creation failed")
            return False
        
        # Step 2: Send verification email
        print("2️⃣ Sending verification email...")
        verification_sent, verification_code = send_verification_email("auth_test@example.com", "auth_test_code_456")
        
        if not verification_sent:
            print("❌ Verification email failed")
            return False
        
        # Step 3: Verify email
        print("3️⃣ Verifying email...")
        verify_success, verify_message = verify_email_code("auth_test@example.com", verification_code)
        
        if not verify_success:
            print(f"❌ Email verification failed: {verify_message}")
            return False
        
        # Step 4: Test authentication
        print("4️⃣ Testing authentication...")
        auth_success, auth_user_id, auth_message = authenticate_user("auth_test@example.com", "SecurePass123!")
        
        if auth_success:
            print("✅ Complete authentication flow successful!")
            print(f"   User ID: {auth_user_id}")
            print(f"   Message: {auth_message}")
            return True
        else:
            print(f"❌ Authentication failed: {auth_message}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing authentication flow: {e}")
        return False

def demonstrate_security_features():
    """Demonstrate security features of the authentication system."""
    print("\n🔒 Security Features Demonstration...")
    
    security_features = [
        "✅ Email verification sent IMMEDIATELY on signup",
        "✅ Account creation ONLY after email verification",
        "✅ No incomplete accounts in the system",
        "✅ Legacy accounts automatically verified (existing users)",
        "✅ Password strength validation",
        "✅ Secure session management with expiry",
        "✅ Firebase Authentication integration",
        "✅ Local authentication fallback",
        "✅ Secure verification code generation",
        "✅ Session timeout protection",
        "✅ Password confirmation validation",
        "✅ Legacy account detection and handling"
    ]
    
    for feature in security_features:
        print(f"   {feature}")
    
    print("\n🚀 **How NEW Signup Flow Works:**")
    print("   1. User fills out signup form and hits 'Send Verification Email'")
    print("   2. System IMMEDIATELY sends verification email (no account created yet)")
    print("   3. User receives verification code in email")
    print("   4. User enters verification code in Email Verification tab")
    print("   5. System verifies email AND creates account simultaneously")
    print("   6. Account is fully active and user can sign in")
    
    print("\n👴 **Legacy Account Handling:**")
    print("   1. EXISTING users can sign in normally")
    print("   2. System detects accounts created before Dec 1, 2024")
    print("   3. Legacy accounts are automatically verified")
    print("   4. No email verification required for existing users")
    print("   5. Seamless transition for current user base")
    
    print("\n💡 **Production Enhancements:**")
    print("   - Integrate with real email service (SendGrid, Mailgun, AWS SES)")
    print("   - Store verification codes in secure database")
    print("   - Implement rate limiting for verification attempts")
    print("   - Add email templates and branding")
    print("   - Enable password reset functionality")

def main():
    """Run all email verification tests."""
    print("🚀 Starting Email Verification System Tests...\n")
    
    # Test imports
    if not test_auth_manager_imports():
        print("❌ Cannot proceed without authentication manager")
        return
    
    # Test Firebase initialization
    firebase_available = test_firebase_initialization()
    
    # Test legacy account detection
    legacy_detection_success = test_legacy_account_detection()
    
    # Test new signup flow
    new_signup_success = test_new_signup_flow()
    
    # Test account creation
    account_created, user_id = test_user_account_creation()
    
    # Test email verification
    verification_success = test_email_verification()
    
    # Test legacy user authentication
    legacy_auth_success = test_legacy_user_authentication()
    
    # Test complete authentication flow
    auth_flow_success = test_authentication_flow()
    
    # Demonstrate security features
    demonstrate_security_features()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"Firebase Available: {'✅ Yes' if firebase_available else '⚠️ No'}")
    print(f"Legacy Detection: {'✅ Success' if legacy_detection_success else '❌ Failed'}")
    print(f"New Signup Flow: {'✅ Success' if new_signup_success else '❌ Failed'}")
    print(f"Account Creation: {'✅ Success' if account_created else '❌ Failed'}")
    print(f"Email Verification: {'✅ Success' if verification_success else '❌ Failed'}")
    print(f"Legacy Auth: {'✅ Success' if legacy_auth_success else '❌ Failed'}")
    print(f"Authentication Flow: {'✅ Success' if auth_flow_success else '❌ Failed'}")
    
    if all([legacy_detection_success, new_signup_success, account_created, verification_success, legacy_auth_success, auth_flow_success]):
        print("\n🎉 All tests passed! Email verification system is working correctly.")
        print("✅ Legacy accounts are properly handled!")
        print("✅ New signup flow works perfectly!")
        print("✅ Email verification happens immediately on signup!")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")
    
    print("\n💡 **Key Benefits of New Flow:**")
    print("   • Verification email sent immediately when user hits signup")
    print("   • No incomplete accounts created in the system")
    print("   • Account only created after email verification")
    print("   • Better user experience and security")
    print("   • Existing users continue using the app without interruption")
    
    print("\n🚀 **Next Steps:**")
    print("   1. Set up Firebase project and configure environment variables")
    print("   2. Integrate with real email service for production use")
    print("   3. Test the system with real email addresses")
    print("   4. Customize email templates and branding")
    print("   5. Monitor legacy account migration success")

if __name__ == "__main__":
    main()
