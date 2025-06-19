import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth, firestore
import os
import json
from functools import wraps
import logging
from datetime import datetime
import requests

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK
firebase_initialized = False

def setup_google_application_credentials():
    """Set up Google Application Credentials from Streamlit secrets or environment"""
    try:
        # First check if GOOGLE_APPLICATION_CREDENTIALS is already set
        if os.getenv("GOOGLE_APPLICATION_CREDENTIALS") and os.path.exists(os.getenv("GOOGLE_APPLICATION_CREDENTIALS")):
            logger.info("Using existing GOOGLE_APPLICATION_CREDENTIALS")
            return
        
        # Try to get from Streamlit secrets
        if hasattr(st, "secrets") and "google_application_credentials_json" in st.secrets:
            creds_dict = dict(st.secrets["google_application_credentials_json"])
            temp_creds_path = "/tmp/google_application_credentials.json"
            
            with open(temp_creds_path, "w") as f:
                json.dump(creds_dict, f)
            
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_creds_path
            logger.info("Set up Google Application Credentials from Streamlit secrets")
        else:
            # Try to find the credentials file in common locations
            possible_paths = [
                "google_application_credentials_key.json",
                "./google_application_credentials_key.json",
                "../google_application_credentials_key.json",
                "/app/google_application_credentials_key.json"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = path
                    logger.info(f"Found credentials at: {path}")
                    return
            
            logger.warning("Could not find Google Application Credentials")
            
    except Exception as e:
        logger.error(f"Error setting up Google Application Credentials: {e}")

def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    global firebase_initialized
    
    if firebase_initialized:
        return
    
    try:
        # Check if already initialized
        try:
            firebase_admin.get_app()
            firebase_initialized = True
            logger.info("Firebase Admin SDK already initialized")
            return
        except ValueError:
            pass
        
        # Set up credentials
        setup_google_application_credentials()
        
        # Initialize Firebase Admin
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred)
        firebase_initialized = True
        logger.info("Firebase Admin SDK initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
        raise

def get_firebase_client_config():
    """Get Firebase client configuration from environment variables"""
    return {
        "apiKey": os.getenv("FIREBASE_API_KEY"),
        "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
        "projectId": os.getenv("FIREBASE_PROJECT_ID"),
        "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
        "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
        "appId": os.getenv("FIREBASE_APP_ID")
    }

def authenticate_user(email, password):
    """Authenticate user with Firebase using REST API"""
    try:
        api_key = os.getenv("FIREBASE_API_KEY")
        if not api_key:
            return None, "Firebase API key not configured"
        
        # Firebase Auth REST API endpoint
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
        
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            # Store the ID token in session state for persistence
            st.session_state["id_token"] = data.get("idToken")
            st.session_state["refresh_token"] = data.get("refreshToken")
            st.session_state["user_uid"] = data.get("localId")
            
            # Get user details from Firebase Admin SDK
            try:
                user = auth.get_user(data.get("localId"))
                return user, "Login successful"
            except Exception as e:
                logger.error(f"Error getting user details: {e}")
                # Return basic user info even if Admin SDK fails
                class BasicUser:
                    def __init__(self, uid, email):
                        self.uid = uid
                        self.email = email
                        self.display_name = email.split('@')[0]
                
                return BasicUser(data.get("localId"), email), "Login successful"
        else:
            error_data = response.json()
            error_message = error_data.get("error", {}).get("message", "Authentication failed")
            return None, error_message
            
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return None, str(e)

def create_user(email, password):
    """Create a new user with Firebase"""
    try:
        # Initialize Firebase if not already done
        initialize_firebase()
        
        # Create user
        user = auth.create_user(
            email=email,
            password=password,
            email_verified=False
        )
        
        # Create user profile in Firestore
        try:
            db = firestore.client()
            user_ref = db.collection('users').document(user.uid)
            user_ref.set({
                'email': email,
                'created_at': firestore.SERVER_TIMESTAMP,
                'display_name': email.split('@')[0],
                'uid': user.uid
            })
        except Exception as e:
            logger.error(f"Error creating user profile in Firestore: {e}")
        
        return user, "Account created successfully! You can now log in."
        
    except auth.EmailAlreadyExistsError:
        return None, "Email already exists. Please login instead."
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return None, str(e)

def verify_session_token():
    """Verify if the stored session token is still valid"""
    try:
        if "id_token" in st.session_state:
            # Verify the ID token
            decoded_token = auth.verify_id_token(st.session_state["id_token"])
            st.session_state["user_uid"] = decoded_token['uid']
            return True
    except Exception as e:
        logger.debug(f"Token verification failed: {e}")
        # Try to refresh the token
        if "refresh_token" in st.session_state:
            return refresh_user_token()
    return False

def refresh_user_token():
    """Refresh the user's authentication token"""
    try:
        api_key = os.getenv("FIREBASE_API_KEY")
        if not api_key or "refresh_token" not in st.session_state:
            return False
        
        url = f"https://securetoken.googleapis.com/v1/token?key={api_key}"
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": st.session_state["refresh_token"]
        }
        
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            st.session_state["id_token"] = data.get("id_token")
            st.session_state["refresh_token"] = data.get("refresh_token")
            return True
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
    
    return False

def is_authenticated():
    """Check if user is authenticated"""
    # First check if we have authentication state
    if st.session_state.get("authenticated", False):
        # Verify the token is still valid
        if verify_session_token():
            return True
        else:
            # Token invalid, clear authentication
            logout()
            return False
    return False

def get_current_user():
    """Get current authenticated user information"""
    if is_authenticated() and "user_uid" in st.session_state:
        try:
            user = auth.get_user(st.session_state["user_uid"])
            return {
                "uid": user.uid,
                "email": user.email,
                "display_name": user.display_name or user.email.split('@')[0],
                "email_verified": user.email_verified,
                "provider": "email"
            }
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            # Return basic info from session
            return {
                "uid": st.session_state.get("user_uid"),
                "email": st.session_state.get("user_email"),
                "display_name": st.session_state.get("user_email", "").split('@')[0],
                "provider": "email"
            }
    return None

def login_required(func):
    """Decorator to require login for certain functions/pages"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            st.warning("Please login to access this page.")
            login_page()
            return None
        return func(*args, **kwargs)
    return wrapper

def logout():
    """Logout the current user"""
    # Clear all authentication-related session state
    auth_keys = [
        "authenticated", "user_email", "user_uid", 
        "id_token", "refresh_token", "auth_message"
    ]
    for key in auth_keys:
        if key in st.session_state:
            del st.session_state[key]
    
    # Clear any cached resources related to the user
    st.cache_data.clear()
    st.success("Logged out successfully!")
    st.rerun()

def login_page():
    """Modern login page matching the screenshot design"""
    
    # Initialize Firebase
    initialize_firebase()
    
    # Custom CSS for the modern login design
    st.markdown(
        """
        <style>
        /* Hide Streamlit default elements */
        .stApp > header {visibility: hidden;}
        .block-container {padding: 0 !important; max-width: 100% !important;}
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Background */
        .stApp {
            background: #e8f4f8;
            min-height: 100vh;
        }
        
        /* Main container */
        .main > div {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 1rem;
        }
        
        /* Login card container */
        [data-testid="stVerticalBlock"] > div:has(.login-header) {
            background: white;
            border-radius: 12px;
            padding: 3rem;
            max-width: 450px;
            width: 100%;
            margin: 0 auto;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
        }
        
        /* Header styling */
        .login-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .login-header h1 {
            font-size: 2.5rem;
            font-weight: 700;
            color: #1a1a1a;
            margin: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        
        /* Lock icon */
        .lock-icon {
            font-size: 3rem;
            margin-bottom: 0.5rem;
        }
        
        /* Welcome text */
        .welcome-text {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .welcome-text h2 {
            font-size: 1.75rem;
            font-weight: 600;
            color: #1a1a1a;
            margin: 0 0 0.5rem 0;
        }
        
        .welcome-text p {
            color: #6b7280;
            font-size: 0.95rem;
            margin: 0;
        }
        
        /* Tabs styling */
        .stTabs {
            margin-bottom: 2rem;
        }
        
        .stTabs [data-baseweb="tab-list"] {
            background: transparent;
            gap: 2rem;
            border-bottom: 2px solid #e5e7eb;
            padding: 0;
        }
        
        .stTabs [data-baseweb="tab"] {
            background: transparent;
            border: none;
            color: #6b7280;
            font-weight: 500;
            font-size: 1rem;
            padding: 0.75rem 0;
            border-bottom: 2px solid transparent;
            margin-bottom: -2px;
        }
        
        .stTabs [aria-selected="true"] {
            color: #f97316 !important;
            border-bottom: 2px solid #f97316 !important;
        }
        
        /* Input fields */
        .stTextInput > label {
            color: #374151;
            font-weight: 500;
            font-size: 0.875rem;
            margin-bottom: 0.5rem;
        }
        
        .stTextInput > div > div > input {
            background: #fef3f2 !important;
            border: 1px solid #fee2e2 !important;
            border-radius: 8px !important;
            padding: 0.75rem 1rem !important;
            font-size: 1rem !important;
            color: #1a1a1a !important;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #f97316 !important;
            outline: none !important;
            box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.1) !important;
        }
        
        /* Buttons */
        .stButton > button {
            background: #4f46e5 !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 0.75rem !important;
            font-size: 1rem !important;
            font-weight: 500 !important;
            width: 100% !important;
            margin: 0.5rem 0 !important;
            cursor: pointer !important;
            transition: background 0.2s ease !important;
        }
        
        .stButton > button:hover {
            background: #4338ca !important;
        }
        
        /* Social buttons */
        .social-button {
            width: 100%;
            padding: 0.75rem;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 500;
            border: none;
            cursor: pointer;
            transition: all 0.2s ease;
            margin: 0.5rem 0;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }
        
        .github-button {
            background: #6366f1;
            color: white;
        }
        
        .github-button:hover {
            background: #5558e3;
        }
        
        .google-button {
            background: #7c3aed;
            color: white;
        }
        
        .google-button:hover {
            background: #6d28d9;
        }
        
        /* Sign up link */
        .signup-link {
            text-align: center;
            margin-top: 2rem;
            color: #6b7280;
            font-size: 0.875rem;
        }
        
        .signup-link a {
            color: #3b82f6;
            text-decoration: none;
            font-weight: 500;
        }
        
        .signup-link a:hover {
            text-decoration: underline;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Create centered container
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Header with lock icon
        st.markdown(
            """
            <div class="login-header">
                <div class="lock-icon">🔒</div>
                <h1>Login or Sign Up</h1>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Tabs for Login and Sign Up
        login_tab, signup_tab = st.tabs(["Login", "Sign Up"])

        with login_tab:
            # Welcome text
            st.markdown(
                """
                <div class="welcome-text">
                    <h2>Login to your account</h2>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Login form
            email = st.text_input("Email", key="login_email", placeholder="Enter your email")
            password = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")
            
            # Forgot password link
            st.markdown(
                """
                <div class="forgot-password-container">
                    <a href="#">Forgot password?</a>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Login button
            if st.button("Login", key="login_button", use_container_width=True):
                if email and password:
                    user, message = authenticate_user(email, password)
                    if user:
                        st.session_state["authenticated"] = True
                        st.session_state["user_email"] = email
                        st.session_state["auth_message"] = "Login successful!"
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.error("❌ Please enter both email and password.")

            # Divider
            st.markdown("<hr style='margin: 2rem 0; border: none; border-top: 1px solid #e5e7eb;'>", unsafe_allow_html=True)

            # Social login info
            st.info("🚧 Social login (GitHub/Google) coming soon!")

        with signup_tab:
            # Welcome text for signup
            st.markdown(
                """
                <div class="welcome-text">
                    <h2>Create your account</h2>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            new_email = st.text_input("Email", key="signup_email", placeholder="Enter your email")
            new_password = st.text_input("Password", type="password", key="signup_password", placeholder="Create a password")
            confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password", placeholder="Confirm your password")

            if st.button("Sign Up", key="signup_button", use_container_width=True):
                if new_email and new_password and confirm_password:
                    if new_password == confirm_password:
                        if len(new_password) >= 6:
                            user, message = create_user(new_email, new_password)
                            if user:
                                st.success(f"✅ {message}")
                                # Auto-login after signup
                                user, login_message = authenticate_user(new_email, new_password)
                                if user:
                                    st.session_state["authenticated"] = True
                                    st.session_state["user_email"] = new_email
                                    st.session_state["auth_message"] = "Account created and logged in!"
                                    st.rerun()
                            else:
                                st.error(f"❌ {message}")
                        else:
                            st.error("❌ Password must be at least 6 characters long.")
                    else:
                        st.error("❌ Passwords do not match.")
                else:
                    st.error("❌ Please fill in all fields.")

            # Divider
            st.markdown("<hr style='margin: 2rem 0; border: none; border-top: 1px solid #e5e7eb;'>", unsafe_allow_html=True)

            # Social signup info
            st.info("🚧 Social signup (GitHub/Google) coming soon!")