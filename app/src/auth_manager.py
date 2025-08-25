#!/usr/bin/env python3
"""
Enhanced Authentication Manager with Email Verification
Uses Firebase Authentication for secure user management
"""

import streamlit as st
import os
import logging
import time
import secrets
from functools import wraps
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

try:
    import extra_streamlit_components as stx
    COOKIE_MANAGER_AVAILABLE = True
except ImportError:
    COOKIE_MANAGER_AVAILABLE = False
    logger.warning("extra_streamlit-omponents not available - persistent authentication disabled")

def get_cookie_manager():
    """"Get cookie manager for persistent authentication"""
    if COOKIE_MANAGER_AVAILABLE:
        return stx.CookieManager()
    return None

# Firebase configuration
FIREBASE_CONFIG = {
    "apiKey": os.getenv("FIREBASE_API_KEY"),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
    "projectId": os.getenv("FIREBASE_PROJECT_ID"),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
    "appId": os.getenv("FIREBASE_APP_ID")
}

# Track when email verification was implemented
EMAIL_VERIFICATION_IMPLEMENTED_DATE = "2024-12-01"  # Date when this feature was added

def setup_google_application_credentials():
    """Set up Google Application Credentials for Firebase Admin SDK"""
    try:
        possible_paths = [
            "multiagentai21-9a8fc-firebase-adminsdk-fbsvc-72f0130c73.json",
            "multiagentai21-key.json",
            "google_application_credentials_key.json",
            os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
        ]
        
        for path in possible_paths:
            if path and os.path.exists(path):
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = path
                logger.info(f"Found credentials at: {path}")
                return path
                
        logger.warning("No Google Application Credentials found")
        return None
                
    except Exception as e:
        logger.error(f"Error setting up credentials: {e}")
        return None

def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        import firebase_admin
        from firebase_admin import credentials, auth
        
        try:
            firebase_admin.get_app()
            logger.info("Firebase already initialized")
            return True
        except ValueError:
            pass
        
        cred_path = setup_google_application_credentials()
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK initialized successfully")
            return True
        else:
            logger.warning("Firebase credentials not found - email verification will be limited")
            return False
            
    except Exception as e:
        logger.error(f"Firebase initialization failed: {e}")
        return False

def is_legacy_account(created_at):
    """Check if an account was created before email verification was implemented."""
    try:
        # If no creation date is available, assume it's a legacy account
        if not created_at:
            logger.info("No creation date found, assuming legacy account")
            return True
        
        # Parse creation date
        if isinstance(created_at, str):
            account_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        else:
            account_date = created_at
        
        # Check if account was created before email verification implementation
        implementation_date = datetime.fromisoformat(EMAIL_VERIFICATION_IMPLEMENTED_DATE)
        
        is_legacy = account_date < implementation_date
        logger.info(f"Account creation date: {account_date}, Implementation date: {implementation_date}, Is legacy: {is_legacy}")
        
        return is_legacy
    except Exception as e:
        logger.warning(f"Error checking if account is legacy: {e}")
        return True
    
    def save_auth_cookie(user_data):
      "Save authentication data to cookies for persistence"""
    try:
        if not COOKIE_MANAGER_AVAILABLE:
            return False
            
        cookie_manager = get_cookie_manager()
        if not cookie_manager:
            return False
        
        # Save authentication data to cookies
        cookie_manager.set(
            "auth_token", 
            user_data.get("auth_token", ""),
            expires_at=datetime.now() + timedelta(days=7)
        )
        cookie_manager.set(
            "user_email", 
            user_data.get("user_email", ""),
            expires_at=datetime.now() + timedelta(days=7)
        )
        cookie_manager.set(
            "user_uid", 
            user_data.get("user_uid", ""),
            expires_at=datetime.now() + timedelta(days=7)
        )
        cookie_manager.set(
            "email_verified", 
            str(user_data.get("email_verified", False)),
            expires_at=datetime.now() + timedelta(days=7)
        )
        cookie_manager.set(
            "is_legacy_account", 
            str(user_data.get("is_legacy_account", False)),
            expires_at=datetime.now() + timedelta(days=7)
        )
        
        logger.info("Authentication data saved to cookies")
        return True
        
    except Exception as e:
        logger.error(f"Error saving auth cookies: {e}")
        return False

def load_auth_cookie():
    """Load authentication data from cookies"""
    try:
        if not COOKIE_MANAGER_AVAILABLE:
            return False
            
        cookie_manager = get_cookie_manager()
        if not cookie_manager:
            return False
        
        # Load authentication data from cookies
        auth_token = cookie_manager.get("auth_token")
        user_email = cookie_manager.get("user_email")
        user_uid = cookie_manager.get("user_uid")
        email_verified = cookie_manager.get("email_verified")
        is_legacy_account = cookie_manager.get("is_legacy_account")
        
        if auth_token and user_email and user_uid:
            # Restore session state from cookies
            st.session_state["authenticated"] = True
            st.session_state["user_email"] = user_email
            st.session_state["user_uid"] = user_uid
            st.session_state["email_verified"] = email_verified == "True"
            st.session_state["is_legacy_account"] = is_legacy_account == "True"
            st.session_state["session_expiry"] = (datetime.now() + timedelta(hours=24)).timestamp()
            
            logger.info("Authentication restored from cookies")
            return True
            
    except Exception as e:
        logger.error(f"Error loading auth cookies: {e}")
    
    return False

def clear_auth_cookies():
    """Clear all authentication cookies"""
    try:
        if not COOKIE_MANAGER_AVAILABLE:
            return
            
        cookie_manager = get_cookie_manager()
        if not cookie_manager:
            return
        
        # Clear authentication cookies
        cookie_manager.delete("auth_token")
        cookie_manager.delete("user_email")
        cookie_manager.delete("user_uid")
        cookie_manager.delete("email_verified")
        cookie_manager.delete("is_legacy_account")
        
        logger.info("Authentication cookies cleared")
        
    except Exception as e:
        logger.error(f"Error clearing auth cookies: {e}")
        
    except Exception as e:
        logger.warning(f"Error checking legacy account status: {e}")
        # On any error, assume it's a legacy account to ensure existing users can access
        return True

def is_authenticated():
    """Check if user is authenticated and email is verified (or legacy account)"""
    # First try to restore from cookies if session is empty
    if not st.session_state.get("authenticated", False):
        if load_auth_cookie():
            # Successfully restored from cookies
            logger.info("Authentication restored from cookies")
    
    if not st.session_state.get("authenticated", False):
        return False
    
    # Check if email is verified OR if it's a legacy account
    email_verified = st.session_state.get("email_verified", False)
    is_legacy = st.session_state.get("is_legacy_account", False)
    
    if not email_verified and not is_legacy:
        return False
    
    # Check if session is still valid
    session_expiry = st.session_state.get("session_expiry")
    if session_expiry and datetime.now().timestamp() > session_expiry:
        logout()
        return False
    
    return True
def get_current_user():
    """Get current authenticated user information"""
    if is_authenticated():
        return {
            "uid": st.session_state.get("user_uid"),
            "email": st.session_state.get("user_email"),
            "display_name": st.session_state.get("user_name"),
            "email_verified": st.session_state.get("email_verified", False),
            "is_legacy_account": st.session_state.get("is_legacy_account", False),
            "provider": "email",
            "created_at": st.session_state.get("user_created_at")
        }
    return None

def login_required(func):
    """Decorator to require login and email verification (or legacy account)"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            login_page()
            return None
        return func(*args, **kwargs)
    return wrapper

def logout():
    """Logout the current user and clear session"""
    auth_keys = [
        "authenticated", "user_email", "user_uid", "user_name", 
        "email_verified", "is_legacy_account", "session_expiry", "user_created_at",
        "verification_sent", "verification_code", "pending_signup"
    ]
    
    for key in auth_keys:
        if key in st.session_state:
            del st.session_state[key]
    
    # Clear authentication cookies
    clear_auth_cookies()
    
    st.success("✅ Logged out successfully!")
    st.rerun()

def create_verification_code():
    """Create a secure verification code"""
    return secrets.token_urlsafe(16)

def send_verification_email(email, verification_code):
    """Send verification email (simulated for now, can be enhanced with real email service)"""
    try:
        # In a real implementation, you would use a service like SendGrid, Mailgun, or AWS SES
        # For now, we'll simulate the email sending and store the code in session
        
        verification_link = f"https://yourdomain.com/verify?email={email}&code={verification_code}"
        
        # Store verification details in session (in production, this would be in a database)
        st.session_state["verification_sent"] = True
        st.session_state["verification_code"] = verification_code
        st.session_state["verification_email"] = email
        st.session_state["verification_expiry"] = (datetime.now() + timedelta(hours=24)).timestamp()
        
        logger.info(f"Verification email sent to {email} with code: {verification_code}")
        
        # In production, you would actually send the email here
        # For demonstration, we'll show the verification code in the UI
        return True, verification_code
        
    except Exception as e:
        logger.error(f"Error sending verification email: {e}")
        return False, str(e)

def verify_email_code(email, code):
    """Verify the email verification code"""
    try:
        stored_code = st.session_state.get("verification_code")
        stored_email = st.session_state.get("verification_email")
        expiry = st.session_state.get("verification_expiry")
        
        if not stored_code or not stored_email or not expiry:
            return False, "Verification code expired or not found"
        
        if datetime.now().timestamp() > expiry:
            return False, "Verification code has expired"
        
        if email != stored_email:
            return False, "Email mismatch"
        
        if code != stored_code:
            return False, "Invalid verification code"
        
        # Mark email as verified
        st.session_state["email_verified"] = True
        
        # Clear verification data
        del st.session_state["verification_sent"]
        del st.session_state["verification_code"]
        del st.session_state["verification_email"]
        del st.session_state["verification_expiry"]
        
        return True, "Email verified successfully!"
        
    except Exception as e:
        logger.error(f"Error verifying email code: {e}")
        return False, f"Verification error: {str(e)}"

def initiate_signup(email, password, display_name):
    """Initiate the signup process by sending verification email first"""
    try:
        # Check if user already exists
        try:
            import firebase_admin
            from firebase_admin import auth
            
            # Check Firebase for existing user
            try:
                user_record = auth.get_user_by_email(email)
                return False, None, "User with this email already exists"
            except auth.UserNotFoundError:
                pass  # User doesn't exist, continue with signup
                
        except ImportError:
            # Fallback to local storage check
            local_users = st.session_state.get("local_users", {})
            if email in local_users:
                return False, None, "User with this email already exists"
        
        # Generate verification code
        verification_code = create_verification_code()
        
        # Send verification email
        verification_sent, sent_code = send_verification_email(email, verification_code)
        
        if verification_sent:
            # Store pending signup information
            st.session_state["pending_signup"] = {
                "email": email,
                "password": password,
                "display_name": display_name,
                "verification_code": sent_code
            }
            
            logger.info(f"Signup initiated for {email}, verification email sent")
            return True, sent_code, "Verification email sent! Please check your email and enter the verification code."
        else:
            return False, None, f"Failed to send verification email: {sent_code}"
            
    except Exception as e:
        logger.error(f"Error initiating signup: {e}")
        return False, None, f"Signup initiation failed: {str(e)}"

def complete_signup_after_verification():
    """Complete the signup process after email verification"""
    try:
        pending_signup = st.session_state.get("pending_signup")
        if not pending_signup:
            return False, None, "No pending signup found"
        
        email = pending_signup["email"]
        password = pending_signup["password"]
        display_name = pending_signup["display_name"]
        
        # Try to use Firebase Admin SDK if available
        try:
            import firebase_admin
            from firebase_admin import auth
            
            # Create user in Firebase
            user_record = auth.create_user(
                email=email,
                password=password,
                display_name=display_name,
                email_verified=True  # Already verified
            )
            
            logger.info(f"Firebase user created: {user_record.uid}")
            
            # Clear pending signup data
            del st.session_state["pending_signup"]
            
            return True, user_record.uid, "Account created successfully! You can now sign in."
                
        except ImportError:
            # Fallback to local storage if Firebase is not available
            logger.info("Firebase not available, using local storage")
            
            # Create local user
            user_id = f"local_{int(time.time())}"
            current_time = datetime.now()
            local_users = st.session_state.get("local_users", {})
            local_users[email] = {
                "uid": user_id,
                "email": email,
                "display_name": display_name,
                "password_hash": hash(password),  # In production, use proper hashing
                "created_at": current_time.isoformat(),
                "email_verified": True,  # Already verified
                "requires_verification": False
            }
            st.session_state["local_users"] = local_users
            
            # Clear pending signup data
            del st.session_state["pending_signup"]
            
            logger.info(f"Local user created: {user_id}")
            return True, user_id, "Account created successfully! You can now sign in."
                
    except Exception as e:
        logger.error(f"Error completing signup: {e}")
        return False, None, f"Account creation failed: {str(e)}"

def create_user_account(email, password, display_name):
    """Create a new user account with Firebase (if available) or local storage"""
    try:
        # Try to use Firebase Admin SDK if available
        try:
            import firebase_admin
            from firebase_admin import auth
            
            # Create user in Firebase
            user_record = auth.create_user(
                email=email,
                password=password,
                display_name=display_name,
                email_verified=False
            )
            
            # Send verification email
            verification_sent, verification_code = send_verification_email(email, verification_code)
            
            if verification_sent:
                logger.info(f"Firebase user created: {user_record.uid}")
                return True, user_record.uid, "Account created successfully! Please check your email for verification."
            else:
                # Delete the Firebase user if email sending failed
                auth.delete_user(user_record.uid)
                return False, None, f"Account creation failed: {verification_code}"
                
        except ImportError:
            # Fallback to local storage if Firebase is not available
            logger.info("Firebase not available, using local storage")
            
            # Check if user already exists
            if email in st.session_state.get("local_users", {}):
                return False, None, "User with this email already exists"
            
            # Create local user
            user_id = f"local_{int(time.time())}"
            current_time = datetime.now()
            local_users = st.session_state.get("local_users", {})
            local_users[email] = {
                "uid": user_id,
                "email": email,
                "display_name": display_name,
                "password_hash": hash(password),  # In production, use proper hashing
                "created_at": current_time.isoformat(),
                "email_verified": False,
                "requires_verification": True  # New accounts require verification
            }
            st.session_state["local_users"] = local_users
            
            # Send verification email
            verification_sent, verification_code = send_verification_email(email, verification_code)
            
            if verification_sent:
                return True, user_id, "Account created successfully! Please check your email for verification."
            else:
                # Remove the local user if email sending failed
                del local_users[email]
                return False, None, f"Account creation failed: {verification_code}"
                
    except Exception as e:
        logger.error(f"Error creating user account: {e}")
        return False, None, f"Account creation failed: {str(e)}"

def authenticate_user(email, password):
    """Authenticate user with Firebase (if available) or local storage"""
    try:
        # Try to use Firebase Admin SDK if available
        try:
            import firebase_admin
            from firebase_admin import auth
            
            # Get user by email
            user_record = auth.get_user_by_email(email)
            
            # In production, you would verify the password here
            # For now, we'll assume the password is correct if the user exists
            
            # Check if email is verified OR if it's a legacy account
            if not user_record.email_verified:
                # Check if this is a legacy account (created before email verification)
                if hasattr(user_record, 'metadata') and user_record.metadata.creation_timestamp:
                    creation_date = datetime.fromtimestamp(user_record.metadata.creation_timestamp / 1000)
                    if is_legacy_account(creation_date):
                        logger.info(f"Legacy account detected for {email}, allowing access")
                        return True, user_record.uid, "Authentication successful (legacy account)"
                else:
                    # No creation timestamp available, assume legacy account
                    logger.info(f"No creation timestamp for {email}, assuming legacy account")
                    return True, user_record.uid, "Authentication successful (legacy account)"
                
                return False, None, "Please verify your email before signing in"
            
            return True, user_record.uid, "Authentication successful"
            
        except ImportError:
            # Fallback to local storage
            local_users = st.session_state.get("local_users", {})
            user_data = local_users.get(email)
            
            if not user_data:
                return False, None, "User not found"
            
            # Check password (in production, use proper password verification)
            if hash(password) != user_data["password_hash"]:
                return False, None, "Invalid password"
            
            # Check if email is verified OR if it's a legacy account
            if not user_data.get("email_verified", False):
                # Check if this is a legacy account
                if is_legacy_account(user_data.get("created_at")):
                    logger.info(f"Legacy account detected for {email}, allowing access")
                    return True, user_data["uid"], "Authentication successful (legacy account)"
                
                return False, None, "Please verify your email before signing in"
            
            return True, user_data["uid"], "Authentication successful"
            
    except Exception as e:
        logger.error(f"Error authenticating user: {e}")
        return False, None, f"Authentication failed: {str(e)}"

def resend_verification_email(email):
    """Resend verification email"""
    try:
        # Check if user exists
        try:
            import firebase_admin
            from firebase_admin import auth
            user_record = auth.get_user_by_email(email)
        except ImportError:
            local_users = st.session_state.get("local_users", {})
            if email not in local_users:
                return False, "User not found"
        
        # Send new verification email
        verification_sent, verification_code = send_verification_email(email, verification_code)
        
        if verification_sent:
            return True, "Verification email sent successfully!"
        else:
            return False, f"Failed to send verification email: {verification_code}"
            
    except Exception as e:
        logger.error(f"Error resending verification email: {e}")
        return False, f"Error resending verification email: {str(e)}"

def handle_legacy_user_login(email, user_id, display_name):
    """Handle login for legacy users (existing accounts before email verification)"""
    try:
        # Set session data for legacy user
        st.session_state["authenticated"] = True
        st.session_state["user_email"] = email
        st.session_state["user_uid"] = user_id
        st.session_state["user_name"] = display_name
        st.session_state["email_verified"] = False  # Legacy accounts don't have verification
        st.session_state["is_legacy_account"] = True  # Mark as legacy account
        st.session_state["user_created_at"] = datetime.now().isoformat()  # Set current time as fallback
        st.session_state["session_expiry"] = (datetime.now() + timedelta(hours=24)).timestamp()
        
        logger.info(f"Legacy user {email} logged in successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error handling legacy user login: {e}")
        return False

def handle_existing_user_login(email, user_id, display_name):
    """Handle login for existing users (treat as legacy accounts)"""
    try:
        # Set session data for existing user
        st.session_state["authenticated"] = True
        st.session_state["user_email"] = email
        st.session_state["user_uid"] = user_id
        st.session_state["user_name"] = display_name
        st.session_state["email_verified"] = True  # Existing accounts are verified
        st.session_state["is_legacy_account"] = True  # Mark as legacy account
        st.session_state["user_created_at"] = datetime.now().isoformat()  # Set current time as fallback
        st.session_state["session_expiry"] = (datetime.now() + timedelta(hours=24)).timestamp()
        
        # Save to cookies for persistence
        save_auth_cookie({
            "user_email": email,
            "user_uid": user_id,
            "email_verified": True,
            "is_legacy_account": True,
            "auth_token": "legacy_user"
        })
        
        logger.info(f"Existing user {email} logged in successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error handling existing user login: {e}")
        return False

def login_page():
    """Enhanced login page with email verification"""
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <h1>🚀 MultiAgentAI21</h1>
        <h2>Advanced Multi-Agent AI System</h2>
        <p style="color: #666; font-size: 1.1rem;">Enhanced agents with actual functionality</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Initialize Firebase
    firebase_available = initialize_firebase()
    
    # Tab selection
    tab1, tab2, tab3 = st.tabs(["🔐 Sign In", "📝 Sign Up", "✅ Email Verification"])
    
    with tab1:
        st.subheader("🔐 Sign In to Access MultiAgentAI21")
        
        if firebase_available:
            st.success("✅ Firebase Authentication Available")
        else:
            st.warning("⚠️ Using Local Authentication (Limited Security)")
        
        st.info("""
        **What's New:**
        • 📊 Data Analysis Agent - Actually processes your CSV files
        • 🤖 Automation Agent - Real file processing and script generation  
        • 📝 Content Creator - Complete, ready-to-use content
        • 💬 Customer Service - Helpful guidance and support
        • 🌐 Web Research - Real-time information and fact-checking
        """)
        
        st.markdown("---")
        
        # Login Form
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="your.email@example.com")
            password = st.text_input("Password", type="password", placeholder="Your password")
            
            col_a, col_b = st.columns(2)
            with col_a:
                login_submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")
            with col_b:
                forgot_password = st.form_submit_button("Forgot Password?", use_container_width=True)
            
            if login_submitted:
                if email and password and len(password) >= 6:
                    success, user_id, message = authenticate_user(email, password)
                    
                    if success:
                        # Check if this is a legacy account
                        if "legacy account" in message.lower():
                            # Handle legacy user login
                            if handle_legacy_user_login(email, user_id, email.split("@")[0]):
                                st.success("✅ Signed in successfully! (Legacy account)")
                                st.info("ℹ️ Your existing account has been automatically verified.")
                                st.rerun()
                            else:
                                st.error("❌ Error processing legacy account login")
                        else:
                            # Regular verified user login
                            st.session_state["authenticated"] = True
                            st.session_state["user_email"] = email
                            st.session_state["user_uid"] = user_id
                            st.session_state["user_name"] = email.split("@")[0]
                            st.session_state["email_verified"] = True
                            st.session_state["is_legacy_account"] = False
                            st.session_state["user_created_at"] = datetime.now().isoformat()
                            st.session_state["session_expiry"] = (datetime.now() + timedelta(hours=24)).timestamp()
                            # Save to cookies for persistence
                            save_auth_cookie({
                                "user_email": email,
                                "user_uid": user_id,
                                "email_verified": True,
                                "is_legacy_account": False,
                                "auth_token": "verified_user"
                            })
                            st.success("✅ Signed in successfully!")
                            st.rerun()
                    else:
                        # Check if this might be an existing account that needs migration
                        if "verify your email" in message.lower():
                            st.error(f"❌ {message}")
                            
                            # Offer to migrate existing account to legacy status
                            st.info("🔍 **Existing Account Detected**")
                            st.info("This appears to be an existing account. Would you like to migrate it to allow access without email verification?")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("🔄 Migrate Account", type="secondary"):
                                    # Create legacy account entry
                                    success, user_id, message = create_legacy_account_from_existing(email, password, email.split("@")[0])
                                    if success:
                                        st.success("✅ Account migrated successfully!")
                                        st.info("You can now sign in with your existing credentials.")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {message}")
                            
                            with col2:
                                if st.button("📧 Verify Email Instead", type="secondary"):
                                    st.info("Please use the Email Verification tab to verify your email address.")
                        else:
                            st.error(f"❌ {message}")
                else:
                    st.error("Please enter valid email and password (6+ characters)")
            
            if forgot_password:
                st.info("Password reset functionality will be implemented in the next version.")
    
    with tab2:
        st.subheader("📝 Create New Account")
        st.info("Create an account to access all MultiAgentAI21 features. Email verification is required for new accounts.")
        
        # Check if there's a pending signup
        pending_signup = st.session_state.get("pending_signup")
        
        if pending_signup:
            # Show pending signup status
            st.info(f"""
            📧 **Verification Email Sent!**
            
            We've sent a verification code to: **{pending_signup['email']}**
            
            Please check your email and enter the verification code in the **Email Verification** tab to complete your account creation.
            """)
            
            # Show verification code for demonstration (in production, this would be hidden)
            if st.session_state.get("verification_code"):
                st.code(f"Verification Code: {st.session_state['verification_code']}")
                st.warning("⚠️ In production, this code would be sent via email, not displayed here.")
            
            # Option to cancel signup
            if st.button("Cancel Signup", type="secondary"):
                del st.session_state["pending_signup"]
                st.rerun()
                
        else:
            # Signup form
            with st.form("signup_form"):
                email = st.text_input("Email Address", placeholder="your.email@example.com")
                password = st.text_input("Password", type="password", placeholder="Choose a strong password (8+ chars)")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
                display_name = st.text_input("Display Name", placeholder="Your preferred name")
                
                # Password strength indicator
                if password:
                    strength = 0
                    if len(password) >= 8:
                        strength += 1
                    if any(c.isupper() for c in password):
                        strength += 1
                    if any(c.islower() for c in password):
                        strength += 1
                    if any(c.isdigit() for c in password):
                        strength += 1
                    if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
                        strength += 1
                    
                    strength_labels = ["Very Weak", "Weak", "Fair", "Good", "Strong"]
                    strength_colors = ["red", "orange", "yellow", "lightgreen", "green"]
                    
                    st.markdown(f"Password Strength: **<span style='color: {strength_colors[strength-1]}'>{strength_labels[strength-1]}</span>**", unsafe_allow_html=True)
                
                signup_submitted = st.form_submit_button("Send Verification Email", use_container_width=True, type="primary")
                
                if signup_submitted:
                    if not all([email, password, confirm_password, display_name]):
                        st.error("Please fill in all fields")
                    elif password != confirm_password:
                        st.error("Passwords do not match")
                    elif len(password) < 8:
                        st.error("Password must be at least 8 characters long")
                    elif strength < 3:
                        st.error("Please choose a stronger password")
                    else:
                        # Initiate signup process
                        success, verification_code, message = initiate_signup(email, password, display_name)
                        
                        if success:
                            st.success("✅ Verification email sent!")
                            st.info("📧 Please check your email for the verification code.")
                            st.info("💡 Go to the Email Verification tab to complete your account creation.")
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
    
    with tab3:
        st.subheader("✅ Email Verification")
        st.info("Verify your email address to complete account creation and access MultiAgentAI21.")
        
        # Check if there's a pending signup
        pending_signup = st.session_state.get("pending_signup")
        
        if pending_signup:
            st.info(f"""
            📝 **Complete Your Signup**
            
            Email: **{pending_signup['email']}**
            Display Name: **{pending_signup['display_name']}**
            
            Enter the verification code from your email to complete account creation.
            """)
            
            # Show verification code for demonstration
            if st.session_state.get("verification_code"):
                st.code(f"Verification Code: {st.session_state['verification_code']}")
                st.warning("⚠️ In production, this code would be sent via email, not displayed here.")
        
        with st.form("verification_form"):
            email = st.text_input("Email Address", placeholder="your.email@example.com", value=pending_signup.get("email", "") if pending_signup else "")
            verification_code = st.text_input("Verification Code", placeholder="Enter the code from your email")
            
            col_a, col_b = st.columns(2)
            with col_a:
                verify_submitted = st.form_submit_button("Verify & Create Account", use_container_width=True, type="primary")
            with col_b:
                resend_submitted = st.form_submit_button("Resend Code", use_container_width=True)
            
            if verify_submitted:
                if email and verification_code:
                    # First verify the email
                    success, message = verify_email_code(email, verification_code)
                    
                    if success:
                        # If verification successful and there's a pending signup, complete it
                        if pending_signup and pending_signup["email"] == email:
                            # Complete the signup process
                            account_created, user_id, create_message = complete_signup_after_verification()
                            
                            if account_created:
                                st.success("✅ Account created successfully!")
                                st.info("🎉 Your account is now active! You can sign in using your email and password.")
                                
                                # Clear any existing verification data
                                if "verification_sent" in st.session_state:
                                    del st.session_state["verification_sent"]
                            else:
                                st.error(f"❌ Account creation failed: {create_message}")
                        else:
                            st.success("✅ Email verified successfully!")
                            st.info("You can now sign in to your account.")
                            
                            # Clear any existing verification data
                            if "verification_sent" in st.session_state:
                                del st.session_state["verification_sent"]
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.error("Please enter both email and verification code")
            
            if resend_submitted:
                if email:
                    success, message = resend_verification_email(email)
                    
                    if success:
                        st.success("✅ Verification email sent!")
                        st.info("Please check your email for the new verification code.")
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.error("Please enter your email address")
        
        # Show verification status if available
        if st.session_state.get("verification_sent"):
            st.info("📧 Verification email sent! Check your email for the verification code.")
        
        # Show verification expiry if available
        if st.session_state.get("verification_expiry"):
            expiry_time = datetime.fromtimestamp(st.session_state["verification_expiry"])
            time_left = expiry_time - datetime.now()
            
            if time_left.total_seconds() > 0:
                hours, remainder = divmod(int(time_left.total_seconds()), 3600)
                minutes, _ = divmod(remainder, 60)
                st.info(f"⏰ Verification code expires in {hours}h {minutes}m")
            else:
                st.error("❌ Verification code has expired. Please request a new one.")
                # Clear expired verification data
                for key in ["verification_sent", "verification_code", "verification_email", "verification_expiry", "pending_signup"]:
                    if key in st.session_state:
                        del st.session_state[key]
        
        # Show legacy account information
        st.info("""
        **ℹ️ Legacy Account Information:**
        • Existing accounts created before December 1, 2024 are automatically verified
        • These accounts can sign in without email verification
        • New accounts require email verification for security
        """)

def check_email_verification_status():
    """Check if the current user's email is verified or if it's a legacy account"""
    if not st.session_state.get("authenticated"):
        return False
    
    email_verified = st.session_state.get("email_verified", False)
    is_legacy = st.session_state.get("is_legacy_account", False)
    
    return email_verified or is_legacy

def require_email_verification(func):
    """Decorator to require email verification (or legacy account)"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not check_email_verification_status():
            st.error("❌ Email verification required")
            st.info("Please verify your email address to access this feature.")
            login_page()
            return None
        return func(*args, **kwargs)
    return wrapper

def migrate_existing_account_to_legacy(email):
    """Migrate an existing account to legacy status to allow access without verification"""
    try:
        # Check if user exists in local storage
        local_users = st.session_state.get("local_users", {})
        if email in local_users:
            # Mark as legacy account
            local_users[email]["is_legacy_account"] = True
            local_users[email]["email_verified"] = True  # Legacy accounts are considered verified
            local_users[email]["requires_verification"] = False
            st.session_state["local_users"] = local_users
            logger.info(f"Migrated {email} to legacy account status")
            return True
        
        # Check Firebase if available
        try:
            import firebase_admin
            from firebase_admin import auth
            
            user_record = auth.get_user_by_email(email)
            if user_record:
                logger.info(f"Found Firebase user {email}, treating as legacy account")
                return True
                
        except ImportError:
            pass
        
        return False
        
    except Exception as e:
        logger.error(f"Error migrating account to legacy: {e}")
        return False

def check_account_exists(email):
    """Check if an account exists in the system"""
    try:
        # Check Firebase if available
        try:
            import firebase_admin
            from firebase_admin import auth
            
            try:
                user_record = auth.get_user_by_email(email)
                return True, "firebase", user_record.uid
            except auth.UserNotFoundError:
                pass
                
        except ImportError:
            pass
        
        # Check local storage
        local_users = st.session_state.get("local_users", {})
        if email in local_users:
            return True, "local", local_users[email]["uid"]
        
        return False, None, None
        
    except Exception as e:
        logger.error(f"Error checking account existence: {e}")
        return False, None, None

def create_legacy_account_from_existing(email, password, display_name):
    """Create a legacy account entry for an existing user"""
    try:
        # Check if account already exists
        exists, account_type, user_id = check_account_exists(email)
        
        if exists and account_type == "firebase":
            # Firebase user exists, mark as legacy
            logger.info(f"Firebase user {email} exists, treating as legacy")
            return True, user_id, "Existing Firebase account detected"
        
        # Create local legacy account
        user_id = f"legacy_{int(time.time())}"
        current_time = datetime.now() - timedelta(days=30)  # Set as created 30 days ago
        
        local_users = st.session_state.get("local_users", {})
        local_users[email] = {
            "uid": user_id,
            "email": email,
            "display_name": display_name or email.split("@")[0],
            "password_hash": hash(password),
            "created_at": current_time.isoformat(),
            "email_verified": True,  # Legacy accounts are verified
            "requires_verification": False,
            "is_legacy_account": True
        }
        st.session_state["local_users"] = local_users
        
        logger.info(f"Created legacy account for {email}")
        return True, user_id, "Legacy account created successfully"
        
    except Exception as e:
        logger.error(f"Error creating legacy account: {e}")
        return False, None, f"Failed to create legacy account: {str(e)}"

