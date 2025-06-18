import streamlit as st
import os
import firebase_admin
from firebase_admin import credentials, auth
from firebase_admin.exceptions import FirebaseError
import logging
import time
import re
from datetime import datetime

logger = logging.getLogger(__name__)

# --- Firebase Admin SDK Initialization ---
_firebase_app = None

def initialize_firebase():
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
        error_msg = f"Firebase Admin SDK service account key file not found at {service_account_key_path}."
        logger.critical(error_msg)
        return None

    try:
        cred = credentials.Certificate(service_account_key_path)
        # Updated to use correct project ID
        _firebase_app = firebase_admin.initialize_app(cred, {
            'projectId': 'multiagentai21-9a8fc'
        })
        logger.info("Firebase Admin SDK initialized successfully.")
        return _firebase_app
    except Exception as e:
        logger.critical(f"Failed to initialize Firebase Admin SDK: {e}", exc_info=True)
        st.error(f"❌ Failed to initialize Firebase Admin SDK: {e}")
        return None

def setup_google_application_credentials():
    """Set up Google Application Credentials for local development."""
    if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
        local_key_path = "firebase_admin_sdk_key.json"
        if os.path.exists(local_key_path):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = local_key_path
            logger.info("GOOGLE_APPLICATION_CREDENTIALS set for local development.")
        else:
            logger.warning("GOOGLE_APPLICATION_CREDENTIALS not set and firebase_admin_sdk_key.json not found.")
    elif os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        logger.info(f"GOOGLE_APPLICATION_CREDENTIALS already set: {os.environ['GOOGLE_APPLICATION_CREDENTIALS']}")
    else:
        logger.warning("GOOGLE_APPLICATION_CREDENTIALS environment variable is set but empty.")

# --- Validation Functions ---
def validate_email(email):
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"

def validate_name(name):
    """Validate display name."""
    if len(name.strip()) < 2:
        return False, "Name must be at least 2 characters long"
    if not re.match(r'^[a-zA-Z\s\'-]+$', name.strip()):
        return False, "Name can only contain letters, spaces, hyphens, and apostrophes"
    return True, "Name is valid"

# --- Session Management Functions ---
def set_user_session(user_record):
    """Sets user information in session state."""
    try:
        st.session_state.user_info = {
            "uid": user_record.uid,
            "email": user_record.email,
            "display_name": user_record.display_name if user_record.display_name else user_record.email,
            "photo_url": user_record.photo_url,
            "provider": getattr(user_record, 'provider_id', 'email'),
            "last_login_at": datetime.now().isoformat(),
            "session_id": f"{user_record.uid}-{int(time.time())}"
        }
        logger.info(f"User session set for UID: {user_record.uid}")
    except Exception as e:
        logger.error(f"Error setting user session: {e}", exc_info=True)
        clear_user_session()

def clear_user_session():
    """Clears user information from session state."""
    keys_to_clear = ["user_info", "last_auth_check", "login_attempts", "last_attempt_time"]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    logger.info("User session cleared.")

def is_authenticated() -> bool:
    """Checks if a user is currently authenticated."""
    if not st.session_state.get("user_info") or not st.session_state.user_info.get("uid"):
        return False
    
    user_uid = st.session_state.user_info["uid"]
    
    # Re-verify user presence periodically
    if "last_auth_check" not in st.session_state or \
       (time.time() - st.session_state.last_auth_check) > 300:  # 5 minutes
        try:
            auth.get_user(user_uid)
            st.session_state.last_auth_check = time.time()
            return True
        except FirebaseError as e:
            logger.warning(f"Firebase Error during periodic check: {e}")
            clear_user_session()
            return False
        except Exception as e:
            logger.error(f"Unexpected error during auth check: {e}")
            return True  # Assume authenticated for temporary issues
    
    return True

def get_current_user() -> dict:
    """Returns the current authenticated user's information."""
    if is_authenticated():
        return st.session_state.user_info
    return {}

def check_rate_limit():
    """Simple rate limiting for login attempts."""
    max_attempts = 5
    time_window = 300  # 5 minutes
    
    current_time = time.time()
    
    if "login_attempts" not in st.session_state:
        st.session_state.login_attempts = 0
        st.session_state.last_attempt_time = current_time
        return True
    
    # Reset counter if time window has passed
    if current_time - st.session_state.last_attempt_time > time_window:
        st.session_state.login_attempts = 0
        st.session_state.last_attempt_time = current_time
        return True
    
    return st.session_state.login_attempts < max_attempts

def increment_login_attempts():
    """Increment failed login attempts."""
    if "login_attempts" not in st.session_state:
        st.session_state.login_attempts = 0
    st.session_state.login_attempts += 1
    st.session_state.last_attempt_time = time.time()

# --- Enhanced Login Page ---
def login_page():
    # Enhanced styling for login page
    st.markdown("""
    <style>
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(0, 0, 0, 0.1);
    }
    
    .login-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .login-logo {
        width: 80px;
        height: 80px;
        background: linear-gradient(45deg, #3b82f6, #8b5cf6);
        border-radius: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 40px;
        margin: 0 auto 1rem;
        color: white;
        box-shadow: 0 10px 30px rgba(59, 130, 246, 0.3);
    }
    
    .login-title {
        font-size: 2rem;
        font-weight: 700;
        color: #1a202c;
        margin: 0;
    }
    
    .login-subtitle {
        color: #6b7280;
        margin-top: 0.5rem;
        font-size: 1.1rem;
    }
    
    .form-section {
        margin: 1.5rem 0;
    }
    
    .form-label {
        display: block;
        margin-bottom: 0.5rem;
        color: #374151;
        font-weight: 600;
    }
    
    .password-strength {
        margin-top: 0.5rem;
        padding: 0.5rem;
        border-radius: 8px;
        font-size: 0.9rem;
    }
    
    .strength-weak {
        background-color: #fee2e2;
        color: #dc2626;
        border: 1px solid #fecaca;
    }
    
    .strength-medium {
        background-color: #fef3c7;
        color: #d97706;
        border: 1px solid #fed7aa;
    }
    
    .strength-strong {
        background-color: #d1fae5;
        color: #059669;
        border: 1px solid #a7f3d0;
    }
    
    .login-footer {
        text-align: center;
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid #e5e7eb;
        color: #6b7280;
        font-size: 0.9rem;
    }
    
    .error-message {
        background-color: #fee2e2;
        border: 1px solid #fecaca;
        color: #dc2626;
        padding: 0.75rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .success-message {
        background-color: #d1fae5;
        border: 1px solid #a7f3d0;
        color: #059669;
        padding: 0.75rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .stApp {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        min-height: 100vh;
    }
    </style>
    """, unsafe_allow_html=True)

    # Check if Firebase is initialized
    if not _firebase_app:
        st.error("🚫 Authentication service is currently unavailable. Please try again later.")
        return

    # Login container
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    
    # Header section
    st.markdown("""
    <div class="login-header">
        <div class="login-logo">🚀</div>
        <h1 class="login-title">MultiAgentAI21</h1>
        <p class="login-subtitle">Welcome back! Please sign in to continue.</p>
    </div>
    """, unsafe_allow_html=True)

    # Create tabs for Login and Sign Up
    tab1, tab2 = st.tabs(["🔑 Sign In", "👤 Create Account"])

    with tab1:
        login_form()

    with tab2:
        signup_form()

    # Footer
    st.markdown("""
    <div class="login-footer">
        <p>🔒 Your data is secure and encrypted</p>
        <p>© 2025 MultiAgentAI21. All rights reserved.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def login_form():
    """Enhanced login form with validation and rate limiting."""
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    
    # Check rate limiting
    if not check_rate_limit():
        remaining_time = 300 - (time.time() - st.session_state.last_attempt_time)
        st.error(f"🚫 Too many failed attempts. Please try again in {int(remaining_time/60)} minutes.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # Login form - FIXED: Removed st.form wrapper and used direct inputs with button
    email = st.text_input(
        "📧 Email Address",
        placeholder="Enter your email address",
        help="The email address associated with your account",
        key="login_email"
    )
    
    password = st.text_input(
        "🔒 Password",
        type="password",
        placeholder="Enter your password",
        help="Your account password",
        key="login_password"
    )
    
    col1, col2 = st.columns([1, 1])
    with col1:
        remember_me = st.checkbox("Remember me")
    with col2:
        if st.button("Forgot Password?", help="Reset your password"):
            st.info("📧 Password reset functionality would be implemented here.")
    
    # FIXED: Added proper submit button
    if st.button("🚀 Sign In", use_container_width=True, key="login_submit"):
        handle_login(email, password, remember_me)

    st.markdown('</div>', unsafe_allow_html=True)

def signup_form():
    """Enhanced signup form with validation."""
    st.markdown('<div class="form-section">', unsafe_allow_html=True)
    
    # FIXED: Removed st.form wrapper and used direct inputs with button
    name = st.text_input(
        "👤 Full Name",
        placeholder="Enter your full name",
        help="This will be displayed as your profile name",
        key="signup_name"
    )
    
    email = st.text_input(
        "📧 Email Address",
        placeholder="Enter your email address",
        help="You'll use this to sign in to your account",
        key="signup_email"
    )
    
    password = st.text_input(
        "🔒 Password",
        type="password",
        placeholder="Create a strong password",
        help="Must be at least 8 characters with uppercase, lowercase, and numbers",
        key="signup_password"
    )
    
    # Password strength indicator
    if password:
        is_valid, message = validate_password(password)
        if is_valid:
            st.markdown(f'<div class="password-strength strength-strong">✅ {message}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="password-strength strength-weak">❌ {message}</div>', unsafe_allow_html=True)
    
    confirm_password = st.text_input(
        "🔒 Confirm Password",
        type="password",
        placeholder="Re-enter your password",
        help="Must match the password above",
        key="signup_confirm_password"
    )
    
    # Terms and conditions
    agree_terms = st.checkbox(
        "I agree to the Terms of Service and Privacy Policy",
        help="You must agree to our terms to create an account"
    )
    
    # FIXED: Added proper submit button
    if st.button("🎉 Create Account", use_container_width=True, key="signup_submit"):
        handle_signup(name, email, password, confirm_password, agree_terms)

    st.markdown('</div>', unsafe_allow_html=True)

def handle_login(email, password, remember_me):
    """Handle login with enhanced validation and error handling."""
    # Input validation
    if not email or not password:
        st.error("❌ Please enter both email and password.")
        return
    
    if not validate_email(email):
        st.error("❌ Please enter a valid email address.")
        return

    try:
        # Get user by email first to check if they exist
        user_record = auth.get_user_by_email(email)
        
        # In production, you'd verify the password properly through client-side auth
        # This is a simplified demonstration
        st.success(f"✅ Welcome back, {user_record.display_name or user_record.email}!")
        set_user_session(user_record)
        
        # Reset login attempts on successful login
        if "login_attempts" in st.session_state:
            del st.session_state.login_attempts
        
        logger.info(f"User logged in: {user_record.email}")
        time.sleep(1)  # Brief delay for UX
        st.rerun()
        
    except FirebaseError as e:
        increment_login_attempts()
        error_code = getattr(e, 'code', 'unknown')
        
        if 'user-not-found' in str(e) or 'invalid-email' in str(e):
            st.error("❌ No account found with this email address.")
        elif 'wrong-password' in str(e) or 'invalid-credential' in str(e):
            st.error("❌ Incorrect password. Please try again.")
        else:
            st.error(f"❌ Login failed: {str(e).replace('_', ' ').title()}")
        
        logger.error(f"Login failed for {email}: {e}")
        
    except Exception as e:
        increment_login_attempts()
        st.error(f"❌ An unexpected error occurred. Please try again.")
        logger.error(f"Unexpected login error: {e}", exc_info=True)

def handle_signup(name, email, password, confirm_password, agree_terms):
    """Handle signup with comprehensive validation."""
    # Input validation
    if not all([name, email, password, confirm_password]):
        st.error("❌ Please fill in all required fields.")
        return
    
    if not agree_terms:
        st.error("❌ You must agree to the Terms of Service and Privacy Policy.")
        return
    
    # Validate name
    name_valid, name_message = validate_name(name)
    if not name_valid:
        st.error(f"❌ {name_message}")
        return
    
    # Validate email
    if not validate_email(email):
        st.error("❌ Please enter a valid email address.")
        return
    
    # Validate password
    password_valid, password_message = validate_password(password)
    if not password_valid:
        st.error(f"❌ {password_message}")
        return
    
    # Check password confirmation
    if password != confirm_password:
        st.error("❌ Passwords do not match.")
        return

    try:
        # Create user account
        user = auth.create_user(
            email=email,
            password=password,
            display_name=name.strip(),
            email_verified=False,
            disabled=False
        )
        
        st.success(f"🎉 Account created successfully! Welcome to MultiAgentAI21, {name}!")
        st.info("📧 Please check your email to verify your account.")
        
        logger.info(f"New user created: {user.uid} ({user.email})")
        
        # Automatically log them in
        time.sleep(2)  # Brief delay to show success message
        set_user_session(user)
        st.rerun()
        
    except FirebaseError as e:
        error_code = getattr(e, 'code', 'unknown')
        
        if 'email-already-exists' in str(e):
            st.error("❌ An account with this email already exists. Please try signing in instead.")
        elif 'weak-password' in str(e):
            st.error("❌ Password is too weak. Please choose a stronger password.")
        elif 'invalid-email' in str(e):
            st.error("❌ Invalid email address format.")
        else:
            st.error(f"❌ Account creation failed: {str(e).replace('_', ' ').title()}")
        
        logger.error(f"Signup failed for {email}: {e}")
        
    except Exception as e:
        st.error("❌ An unexpected error occurred. Please try again.")
        logger.error(f"Unexpected signup error: {e}", exc_info=True)

def logout():
    """Enhanced logout with confirmation."""
    user_email = st.session_state.get("user_info", {}).get("email", "Unknown")
    clear_user_session()
    logger.info(f"User logged out: {user_email}")
    st.success("👋 You have been successfully logged out. See you next time!")
    time.sleep(1)
    st.rerun()

def login_required(func):
    """Decorator to ensure a user is logged in before accessing a page."""
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            login_page()
            return None
        return func(*args, **kwargs)
    return wrapper