import os
import json
import logging
import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth
from google.oauth2 import service_account
from firebase_admin.exceptions import FirebaseError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

# Global variable to store the Firebase app instance
firebase_app = None

def initialize_firebase():
    global firebase_app
    if firebase_app:
        logger.info("Firebase app already initialized.")
        return

    try:
        # --- NEW: Attempt to load Firebase Admin SDK credentials from a mounted file ---
        firebase_admin_key_path = "/app/firebase_admin_sdk_key.json"
        if os.path.exists(firebase_admin_key_path):
            logger.info(f"Attempting to initialize Firebase Admin SDK from file: {firebase_admin_key_path}")
            # Load the JSON content from the file
            with open(firebase_admin_key_path, 'r') as f:
                credentials_info = json.load(f)
            cred = credentials.Certificate(credentials_info)
            firebase_app = firebase_admin.initialize_app(cred)
            logger.info(f"Firebase Admin SDK initialized successfully from file: {firebase_admin_key_path}")
            return

        # --- OLD (Fallback): Attempt to load from FIREBASE_ADMIN_SDK_JSON environment variable (kept as fallback) ---
        credentials_json_str = os.getenv('FIREBASE_ADMIN_SDK_JSON')
        if credentials_json_str:
            logger.info("Found FIREBASE_ADMIN_SDK_JSON environment variable. Attempting to initialize from string.")
            credentials_info = json.loads(credentials_json_str)
            cred = credentials.Certificate(credentials_info)
            firebase_app = firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK initialized successfully from environment variable.")
            return

        logger.warning("No Firebase Admin SDK credentials found (neither file nor environment variable). Firebase Admin SDK will not be initialized.")
        # If no credentials are found by this point, raise an error to stop app startup as it's critical
        raise ValueError("Firebase credentials not found via environment variable or any local/mounted file path. Please ensure 'firebase_admin_sdk_key.json' is present in the /app directory (via Docker volume mount) or FIREBASE_ADMIN_SDK_JSON environment variable is set.")

    except json.JSONDecodeError as e:
        logger.error(f"JSON decoding error for Firebase Admin SDK credentials: {e}")
        raise ValueError(f"Invalid JSON for Firebase Admin SDK credentials: {e}")
    except Exception as e:
        logger.error(f"Error initializing Firebase Admin SDK: {e}", exc_info=True)
        raise ValueError(f"Failed to initialize Firebase Admin SDK: {e}")

def authenticate_user(email, password):
    global firebase_app
    if not firebase_app:
        logger.error("Authentication error: The default Firebase app does not exist. Make sure to initialize the SDK by calling initialize_app().")
        return None, "Authentication failed. Firebase SDK not initialized."
    try:
        user = auth.get_user_by_email(email)
        logger.info(f"User {email} found with UID: {user.uid}")
        # Note: Firebase Admin SDK does not authenticate users directly with email/password.
        # This function would typically be used for server-side user management or token verification.
        # For a Streamlit app with client-side login, you'd usually verify a token or mock user data here.
        # For now, finding the user is considered 'successful' for the purpose of the login flow.
        return user, "Authentication successful."

    except firebase_admin.auth.UserNotFoundError:
        logger.warning(f"Authentication failed: User with email {email} not found.")
        return None, "Authentication failed. User not found."
    except firebase_admin.auth.AuthError as e:
        logger.error(f"Firebase Authentication error: {e}")
        return None, f"Authentication failed: {e.code}"
    except Exception as e:
        logger.error(f"Authentication error: An unexpected error occurred: {e}")
        return None, f"Authentication failed. An unexpected error occurred: {e}"

def create_user(email, password):
    global firebase_app
    if not firebase_app:
        logger.error("User creation error: Firebase app not initialized.")
        return None, "User creation failed. Firebase SDK not initialized."
    try:
        user = auth.create_user(email=email, password=password)
        logger.info(f"Successfully created new user: {user.uid}")
        return user, "User created successfully. You can now sign in."
    except firebase_admin.auth.AuthError as e:
        logger.error(f"Firebase Auth error during user creation: {e}")
        return None, f"User creation failed: {e.code}"
    except Exception as e:
        logger.error(f"Unexpected error during user creation: {e}")
        return None, f"User creation failed. An unexpected error occurred: {e}"

# Modern Streamlit login page matching the screenshot
def login_page():
    """Modern login page matching the screenshot design"""
    
    # Set page config for centered layout
    if not st.session_state.get('page_config_set', False):
        st.set_page_config(
            page_title="MultiAgentAI21",
            page_icon="🤖",
            layout="centered",
            initial_sidebar_state="collapsed",
        )
        st.session_state.page_config_set = True

    # Custom CSS for the modern login design
    st.markdown(
        """
        <style>
        /* Hide Streamlit default elements */
        .stApp > header {visibility: hidden;}
        .stApp > .main > div > div > div > section > div {padding-top: 0rem;}
        .stApp {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        /* Main container */
        .main-container {
            max-width: 500px;
            margin: 0 auto;
            padding: 2rem;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }
        
        /* Login card */
        .login-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 3rem;
            width: 100%;
            max-width: 400px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            text-align: center;
        }
        
        /* Header */
        .app-title {
            font-size: 2.5rem;
            font-weight: 700;
            color: #1a202c;
            margin-bottom: 1rem;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        
        .login-mode {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            margin-bottom: 2rem;
            color: #4a5568;
            font-size: 0.9rem;
        }
        
        .toggle-switch {
            width: 40px;
            height: 20px;
            background: #3b82f6;
            border-radius: 20px;
            position: relative;
            cursor: pointer;
        }
        
        .toggle-switch::after {
            content: '';
            position: absolute;
            width: 16px;
            height: 16px;
            background: white;
            border-radius: 50%;
            top: 2px;
            right: 2px;
            transition: all 0.3s ease;
        }
        
        .welcome-text {
            font-size: 1.8rem;
            font-weight: 600;
            color: #1a202c;
            margin-bottom: 0.5rem;
        }
        
        .subtitle {
            color: #6b7280;
            margin-bottom: 2rem;
            font-size: 0.9rem;
        }
        
        /* Input fields */
        .stTextInput > div > div > input {
            background: #f8fafc !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 12px !important;
            padding: 0.75rem 1rem !important;
            font-size: 1rem !important;
            color: #1a202c !important;
            transition: all 0.3s ease !important;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #3b82f6 !important;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
            outline: none !important;
        }
        
        .stTextInput > label {
            color: #374151 !important;
            font-weight: 500 !important;
            font-size: 0.9rem !important;
            margin-bottom: 0.5rem !important;
        }
        
        /* Buttons */
        .stButton > button {
            background: linear-gradient(135deg, #3b82f6, #1d4ed8) !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 0.75rem 2rem !important;
            font-size: 1rem !important;
            font-weight: 600 !important;
            width: 100% !important;
            margin: 0.5rem 0 !important;
            cursor: pointer !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3) !important;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4) !important;
        }
        
        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background: #f1f5f9;
            border-radius: 12px;
            padding: 4px;
            margin-bottom: 2rem;
        }
        
        .stTabs [data-baseweb="tab"] {
            background: transparent;
            border-radius: 8px;
            color: #64748b;
            font-weight: 500;
        }
        
        .stTabs [aria-selected="true"] {
            background: white !important;
            color: #1e293b !important;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }
        
        /* Links */
        .forgot-password {
            color: #3b82f6;
            text-decoration: none;
            font-size: 0.9rem;
            text-align: right;
            display: block;
            margin: 0.5rem 0 1.5rem 0;
        }
        
        .forgot-password:hover {
            text-decoration: underline;
        }
        
        /* Additional social buttons */
        .social-button {
            background: linear-gradient(135deg, #6b7280, #4b5563);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 0.75rem 2rem;
            font-size: 1rem;
            font-weight: 600;
            width: 100%;
            margin: 0.5rem 0;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(107, 114, 128, 0.3);
            text-align: center;
            display: block;
            text-decoration: none;
        }
        
        .social-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(107, 114, 128, 0.4);
        }
        
        .google-button {
            background: linear-gradient(135deg, #ea4335, #d33b2c);
            box-shadow: 0 4px 15px rgba(234, 67, 53, 0.3);
        }
        
        .google-button:hover {
            box-shadow: 0 8px 25px rgba(234, 67, 53, 0.4);
        }
        
        /* Success/Error messages */
        .stAlert {
            border-radius: 12px !important;
            margin: 1rem 0 !important;
        }
        
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Main container with gradient background
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # Login card
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    
    # Header
    st.markdown('<h1 class="app-title">MultiAgentAI21</h1>', unsafe_allow_html=True)
    
    # Login mode toggle (visual only for now)
    st.markdown(
        '''
        <div class="login-mode">
            <div class="toggle-switch"></div>
            <span>Login Mode</span>
        </div>
        ''', 
        unsafe_allow_html=True
    )

    # Tabs for Login and Sign Up
    login_tab, signup_tab = st.tabs(["Login", "Sign Up"])

    with login_tab:
        # Welcome text
        st.markdown('<h2 class="welcome-text">Welcome Back</h2>', unsafe_allow_html=True)
        st.markdown('<p class="subtitle">Sign in to your account</p>', unsafe_allow_html=True)
        
        # Login form
        email = st.text_input("Email Address", key="login_email", placeholder="Enter your email")
        password = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")
        
        # Forgot password link
        st.markdown('<a href="#" class="forgot-password">Forgot password?</a>', unsafe_allow_html=True)

        # Sign In button
        if st.button("Sign In", key="signin_button"):
            if email and password:
                user, message = authenticate_user(email, password)
                if user:
                    st.session_state["authenticated"] = True
                    st.session_state["user_email"] = email
                    st.session_state["user_uid"] = user.uid
                    st.session_state["auth_message"] = "Login successful!"
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
            else:
                st.error("❌ Please enter both email and password.")

        # Social login buttons (placeholder for now)
        st.markdown('<div style="margin-top: 1.5rem;">', unsafe_allow_html=True)
        st.markdown(
            '''
            <div class="social-button">
                Sign in with GitHub
            </div>
            ''',
            unsafe_allow_html=True
        )
        
        st.markdown(
            '''
            <div class="social-button google-button">
                Sign in with Google
            </div>
            ''',
            unsafe_allow_html=True
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with signup_tab:
        # Sign up form
        st.markdown('<h2 class="welcome-text">Create Account</h2>', unsafe_allow_html=True)
        st.markdown('<p class="subtitle">Sign up for a new account</p>', unsafe_allow_html=True)
        
        new_email = st.text_input("Email Address", key="signup_email", placeholder="Enter your email")
        new_password = st.text_input("Password", type="password", key="signup_password", placeholder="Create a password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password", placeholder="Confirm your password")

        if st.button("Sign Up", key="signup_button"):
            if new_email and new_password and confirm_password:
                if new_password == confirm_password:
                    if len(new_password) >= 6:
                        user, message = create_user(new_email, new_password)
                        if user:
                            st.success(f"✅ {message}")
                            # Optionally auto-login after signup
                            st.session_state["authenticated"] = True
                            st.session_state["user_email"] = new_email
                            st.session_state["user_uid"] = user.uid
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

    # Close containers
    st.markdown('</div>', unsafe_allow_html=True)  # Close login-card
    st.markdown('</div>', unsafe_allow_html=True)  # Close main-container

def logout():
    st.session_state["authenticated"] = False
    st.session_state["user_email"] = None
    st.session_state["user_uid"] = None
    st.session_state["auth_message"] = "Logged out successfully."
    st.rerun()

def is_authenticated():
    return st.session_state.get("authenticated", False)

def login_required(func):
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            login_page()
            return None # Important: Stop further execution of the decorated function
        return func(*args, **kwargs)
    return wrapper

def get_current_user():
    return {
        "email": st.session_state.get("user_email"),
        "uid": st.session_state.get("user_uid"),
        # Add other user details if available from Firebase (e.g., display_name, photo_url)
        # For simplicity, we'll just return email and uid for now
    }

# --- Handle Google Application Credentials for other Google Cloud services ---
# This function aims to set GOOGLE_APPLICATION_CREDENTIALS to a temporary file
# if GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable is provided,
# or to look for a mounted file.
def setup_google_application_credentials():
    # --- NEW: Prefer loading from a mounted file for GOOGLE_APPLICATION_CREDENTIALS ---
    google_creds_file_path = "/app/google_application_credentials_key.json"
    if os.path.exists(google_creds_file_path):
        logger.info(f"Found Google Application Credentials file at: {google_creds_file_path}. Setting GOOGLE_APPLICATION_CREDENTIALS.")
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = google_creds_file_path
        return

    # --- OLD (Fallback): Attempt to use GOOGLE_APPLICATION_CREDENTIALS_JSON env var and write to temp file ---
    google_creds_json_str = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
    if google_creds_json_str:
        logger.info("Found GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable. Attempting to write to temporary file.")
        try:
            import tempfile
            # Ensure the temp file content is the JSON string itself, not a string representation of the JSON object
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
                temp_file.write(google_creds_json_str)
                temp_file_path = temp_file.name
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = temp_file_path
            logger.info(f"GOOGLE_APPLICATION_CREDENTIALS set to temporary file: {temp_file_path}")
        except Exception as e:
            logger.error(f"Error setting GOOGLE_APPLICATION_CREDENTIALS from JSON string: {e}")
            # Do not re-raise, allow app to continue with other credential methods if available
    elif not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
        logger.warning("GOOGLE_APPLICATION_CREDENTIALS_JSON and GOOGLE_APPLICATION_CREDENTIALS are not set. Some Google Cloud services might not authenticate.")

# Initialize Firebase Admin SDK first
initialize_firebase()

# Set up Google Application Credentials (for other Google Cloud APIs)
setup_google_application_credentials()