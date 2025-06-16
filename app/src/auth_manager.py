import streamlit as st
import os
import firebase_admin
from firebase_admin import credentials, auth
import logging
import time
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from functools import wraps

logger = logging.getLogger(__name__)

# --- Configuration ---
SESSION_TIMEOUT = 3600  # 1 hour in seconds
AUTH_CHECK_INTERVAL = 300  # 5 minutes in seconds
MIN_PASSWORD_LENGTH = 8

# --- Firebase Admin SDK Initialization ---
_firebase_app = None

def initialize_firebase():
    """Initialize Firebase Admin SDK with proper error handling."""
    global _firebase_app
    if _firebase_app:
        logger.info("Firebase Admin SDK already initialized.")
        return _firebase_app

    service_account_key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not service_account_key_path:
        error_msg = "GOOGLE_APPLICATION_CREDENTIALS environment variable is not set."
        logger.critical(error_msg)
        return None
    
    if not os.path.exists(service_account_key_path):
        error_msg = f"Firebase Admin SDK service account key file not found at {service_account_key_path}"
        logger.critical(error_msg)
        return None

    try:
        cred = credentials.Certificate(service_account_key_path)
        _firebase_app = firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized successfully.")
        return _firebase_app
    except Exception as e:
        logger.critical(f"Failed to initialize Firebase Admin SDK: {e}", exc_info=True)
        return None

def setup_google_application_credentials():
    """Set up Google Application Credentials for local development."""
    if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
        local_key_path = "firebase_admin_sdk_key.json"
        if os.path.exists(local_key_path):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = local_key_path
            logger.info("GOOGLE_APPLICATION_CREDENTIALS set for local development.")
        else:
            logger.warning("Firebase service account key not found for local development.")
    else:
        logger.info(f"GOOGLE_APPLICATION_CREDENTIALS already set: {os.environ['GOOGLE_APPLICATION_CREDENTIALS']}")

# --- Security Utilities ---
def generate_session_token() -> str:
    """Generate a secure session token."""
    return secrets.token_urlsafe(32)

def hash_password(password: str, salt: str) -> str:
    """Hash password with salt (for additional security layers)."""
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)

def validate_email(email: str) -> bool:
    """Basic email validation."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength."""
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters long"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    
    return True, "Password is valid"

# --- Session Management ---
def create_session_data(user_record) -> Dict[str, Any]:
    """Create secure session data."""
    current_time = datetime.now()
    return {
        "uid": user_record.uid,
        "email": user_record.email,
        "display_name": user_record.display_name or user_record.email,
        "photo_url": user_record.photo_url,
        "email_verified": user_record.email_verified,
        "created_at": current_time.isoformat(),
        "expires_at": (current_time + timedelta(seconds=SESSION_TIMEOUT)).isoformat(),
        "session_token": generate_session_token(),
        "last_activity": current_time.isoformat()
    }

def set_user_session(user_record):
    """Set user session with enhanced security."""
    try:
        session_data = create_session_data(user_record)
        st.session_state.user_session = session_data
        st.session_state.last_auth_check = time.time()
        logger.info(f"User session created for UID: {user_record.uid}")
    except Exception as e:
        logger.error(f"Error setting user session: {e}", exc_info=True)
        clear_user_session()

def clear_user_session():
    """Clear user session data."""
    session_keys = ['user_session', 'last_auth_check', 'login_attempts']
    for key in session_keys:
        if key in st.session_state:
            del st.session_state[key]
    logger.info("User session cleared.")

def is_session_expired() -> bool:
    """Check if current session has expired."""
    if not st.session_state.get("user_session"):
        return True
    
    try:
        expires_at = datetime.fromisoformat(st.session_state.user_session["expires_at"])
        return datetime.now() > expires_at
    except (KeyError, ValueError):
        return True

def refresh_session():
    """Refresh session expiration time."""
    if st.session_state.get("user_session"):
        current_time = datetime.now()
        st.session_state.user_session["expires_at"] = (current_time + timedelta(seconds=SESSION_TIMEOUT)).isoformat()
        st.session_state.user_session["last_activity"] = current_time.isoformat()

def is_authenticated() -> bool:
    """Check if user is authenticated with comprehensive validation."""
    if not st.session_state.get("user_session"):
        logger.debug("No user session found.")
        return False
    
    if is_session_expired():
        logger.info("Session expired.")
        clear_user_session()
        st.warning("Your session has expired. Please log in again.")
        return False
    
    user_uid = st.session_state.user_session.get("uid")
    if not user_uid:
        logger.warning("No UID in session.")
        clear_user_session()
        return False
    
    # Periodic Firebase verification
    current_time = time.time()
    last_check = st.session_state.get("last_auth_check", 0)
    
    if (current_time - last_check) > AUTH_CHECK_INTERVAL:
        logger.info(f"Performing periodic authentication check for user: {user_uid}")
        try:
            user_record = auth.get_user(user_uid)
            if user_record.disabled:
                logger.warning(f"User account {user_uid} is disabled.")
                clear_user_session()
                st.error("Your account has been disabled. Please contact support.")
                return False
            
            st.session_state.last_auth_check = current_time
            refresh_session()  # Refresh session on successful verification
            logger.debug(f"User {user_uid} verified and session refreshed.")
            
        except firebase_admin.auth.AuthError as e:
            logger.warning(f"Firebase Auth Error during periodic check: {e}")
            clear_user_session()
            st.error("Authentication error. Please log in again.")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during auth check: {e}", exc_info=True)
            # Don't clear session for unexpected errors
            pass
    
    return True

def get_current_user() -> Dict[str, Any]:
    """Get current authenticated user information."""
    if is_authenticated():
        return st.session_state.user_session
    return {}

# --- Rate Limiting ---
def check_rate_limit(action: str, max_attempts: int = 5, window_minutes: int = 15) -> bool:
    """Check if action is rate limited."""
    if "rate_limits" not in st.session_state:
        st.session_state.rate_limits = {}
    
    current_time = time.time()
    window_seconds = window_minutes * 60
    
    if action not in st.session_state.rate_limits:
        st.session_state.rate_limits[action] = []
    
    # Clean old attempts
    st.session_state.rate_limits[action] = [
        timestamp for timestamp in st.session_state.rate_limits[action]
        if current_time - timestamp < window_seconds
    ]
    
    if len(st.session_state.rate_limits[action]) >= max_attempts:
        return False
    
    st.session_state.rate_limits[action].append(current_time)
    return True

# --- Authentication Functions ---
def verify_id_token(id_token: str) -> Optional[Dict[str, Any]]:
    """Verify Firebase ID token (for production use with client-side auth)."""
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        logger.error(f"ID token verification failed: {e}")
        return None

def authenticate_user(email: str, password: str) -> tuple[bool, str, Optional[Any]]:
    """Authenticate user (simplified for demo - use client-side Firebase Auth in production)."""
    if not validate_email(email):
        return False, "Invalid email format", None
    
    if not check_rate_limit("login", max_attempts=5, window_minutes=15):
        return False, "Too many login attempts. Please try again later.", None
    
    try:
        # In production, this should be handled client-side with Firebase Auth
        # This is a simplified demo that only checks if user exists
        user_record = auth.get_user_by_email(email)
        
        if user_record.disabled:
            return False, "Account is disabled. Please contact support.", None
        
        # In a real implementation, password verification would happen client-side
        # and you'd verify the ID token here instead
        return True, "Login successful", user_record
        
    except firebase_admin.auth.AuthError as e:
        error_message = "Invalid email or password"
        if e.code == "USER_NOT_FOUND_ERROR":
            error_message = "No account found with this email"
        logger.error(f"Authentication error: {e}")
        return False, error_message, None
    except Exception as e:
        logger.error(f"Unexpected authentication error: {e}", exc_info=True)
        return False, "An unexpected error occurred", None

def create_user_account(name: str, email: str, password: str) -> tuple[bool, str, Optional[Any]]:
    """Create new user account with validation."""
    if not name.strip():
        return False, "Name is required", None
    
    if not validate_email(email):
        return False, "Invalid email format", None
    
    is_valid, password_message = validate_password(password)
    if not is_valid:
        return False, password_message, None
    
    if not check_rate_limit("signup", max_attempts=3, window_minutes=60):
        return False, "Too many signup attempts. Please try again later.", None
    
    try:
        user = auth.create_user(
            email=email,
            password=password,
            display_name=name.strip(),
            email_verified=False,
            disabled=False
        )
        logger.info(f"New user created: {user.uid} ({user.email})")
        return True, "Account created successfully", user
        
    except firebase_admin.auth.AuthError as e:
        error_message = "Failed to create account"
        if e.code == "EMAIL_ALREADY_EXISTS_ERROR":
            error_message = "An account with this email already exists"
        elif e.code == "WEAK_PASSWORD_ERROR":
            error_message = "Password is too weak"
        logger.error(f"User creation error: {e}")
        return False, error_message, None
    except Exception as e:
        logger.error(f"Unexpected user creation error: {e}", exc_info=True)
        return False, "An unexpected error occurred", None

# --- UI Components ---
def login_page():
    """Enhanced login page with better UX and security."""
    if not hasattr(st, '_page_config_set') or not st.session_state.get('_page_config_set', False):
        st.set_page_config(
            page_title="MultiAgentAI21 - Authentication",
            page_icon="🔒",
            layout="centered",
            initial_sidebar_state="collapsed",
        )
        st.session_state._page_config_set = True

    st.title("🔒 Welcome to MultiAgentAI21")
    
    if not _firebase_app:
        st.error("🚫 Authentication service is unavailable. Please try again later.")
        if st.button("Retry Initialization"):
            initialize_firebase()
            st.rerun()
        return

    # Create tabs for login and signup
    login_tab, signup_tab = st.tabs(["🔑 Login", "📝 Sign Up"])

    with login_tab:
        st.subheader("Sign in to your account")
        
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("📧 Email", placeholder="Enter your email address")
            password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                login_button = st.form_submit_button("🚀 Login", use_container_width=True)
            with col2:
                forgot_password = st.form_submit_button("❓ Forgot Password?", use_container_width=True)

            if login_button:
                if not email or not password:
                    st.error("📝 Please fill in all fields")
                else:
                    with st.spinner("Authenticating..."):
                        success, message, user_record = authenticate_user(email, password)
                        
                    if success and user_record:
                        st.success(f"✅ Welcome back, {user_record.display_name or user_record.email}!")
                        set_user_session(user_record)
                        time.sleep(1)  # Brief pause for UX
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")

            if forgot_password:
                st.info("🔄 Password reset functionality would be implemented here using Firebase Auth client-side SDK")

    with signup_tab:
        st.subheader("Create your account")
        
        with st.form("signup_form", clear_on_submit=False):
            name = st.text_input("👤 Full Name", placeholder="Enter your full name")
            email = st.text_input("📧 Email", placeholder="Enter your email address")
            password = st.text_input("🔒 Password", type="password", placeholder="Create a strong password")
            confirm_password = st.text_input("🔒 Confirm Password", type="password", placeholder="Confirm your password")
            
            # Password requirements
            st.caption("Password must contain at least 8 characters, including uppercase, lowercase, and numbers")
            
            terms_accepted = st.checkbox("✅ I agree to the Terms of Service and Privacy Policy")
            
            signup_button = st.form_submit_button("🎯 Create Account", use_container_width=True)

            if signup_button:
                if not all([name, email, password, confirm_password]):
                    st.error("📝 Please fill in all fields")
                elif password != confirm_password:
                    st.error("🔄 Passwords do not match")
                elif not terms_accepted:
                    st.error("📋 Please accept the Terms of Service")
                else:
                    with st.spinner("Creating your account..."):
                        success, message, user_record = create_user_account(name, email, password)
                    
                    if success:
                        st.success(f"🎉 {message} Please sign in with your new account.")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")

def logout():
    """Enhanced logout function."""
    if st.session_state.get("user_session"):
        user_email = st.session_state.user_session.get("email", "Unknown")
        clear_user_session()
        logger.info(f"User logged out: {user_email}")
        st.success("👋 You have been logged out successfully.")
        time.sleep(1)
    st.rerun()

def login_required(func):
    """Decorator to require authentication for protected functions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            login_page()
            return None
        return func(*args, **kwargs)
    return wrapper

# --- User Profile Management ---
def update_user_profile(display_name: str = None, photo_url: str = None) -> tuple[bool, str]:
    """Update user profile information."""
    if not is_authenticated():
        return False, "User not authenticated"
    
    try:
        uid = st.session_state.user_session["uid"]
        update_data = {}
        
        if display_name:
            update_data["display_name"] = display_name.strip()
        if photo_url:
            update_data["photo_url"] = photo_url.strip()
        
        if update_data:
            auth.update_user(uid, **update_data)
            # Update session data
            st.session_state.user_session.update(update_data)
            return True, "Profile updated successfully"
        
        return False, "No changes to update"
        
    except Exception as e:
        logger.error(f"Profile update error: {e}", exc_info=True)
        return False, "Failed to update profile"

def change_user_password(new_password: str) -> tuple[bool, str]:
    """Change user password (admin function)."""
    if not is_authenticated():
        return False, "User not authenticated"
    
    is_valid, password_message = validate_password(new_password)
    if not is_valid:
        return False, password_message
    
    try:
        uid = st.session_state.user_session["uid"]
        auth.update_user(uid, password=new_password)
        logger.info(f"Password changed for user: {uid}")
        return True, "Password changed successfully"
        
    except Exception as e:
        logger.error(f"Password change error: {e}", exc_info=True)
        return False, "Failed to change password"

# Initialize Firebase on module import
initialize_firebase()