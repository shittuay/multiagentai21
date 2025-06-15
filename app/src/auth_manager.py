import os
import json
import logging
import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth
from google.oauth2 import service_account

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
        # Attempt to load Firebase Admin SDK credentials from a mounted file
        firebase_admin_key_path = "/app/firebase_admin_sdk_key.json"
        if os.path.exists(firebase_admin_key_path):
            logger.info(f"Attempting to initialize Firebase Admin SDK from file: {firebase_admin_key_path}")
            with open(firebase_admin_key_path, 'r') as f:
                credentials_info = json.load(f)
            cred = credentials.Certificate(credentials_info)
            firebase_app = firebase_admin.initialize_app(cred)
            logger.info(f"Firebase Admin SDK initialized successfully from file: {firebase_admin_key_path}")
            return

        # Fallback: Attempt to load from FIREBASE_ADMIN_SDK_JSON environment variable
        credentials_json_str = os.getenv('FIREBASE_ADMIN_SDK_JSON')
        if credentials_json_str:
            logger.info("Found FIREBASE_ADMIN_SDK_JSON environment variable. Attempting to initialize from string.")
            credentials_info = json.loads(credentials_json_str)
            cred = credentials.Certificate(credentials_info)
            firebase_app = firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK initialized successfully from environment variable.")
            return

        logger.warning("No Firebase Admin SDK credentials found (neither file nor environment variable). Firebase Admin SDK will not be initialized.")
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
        # This part of the authentication is still conceptual for client-side login
        # Firebase Admin SDK is for server-side operations.
        # For a full client-side login, you'd typically use Firebase JS SDK in a web frontend
        # and verify the token on the backend if needed.
        # Here, we're just checking if a user exists with that email for demonstration purposes.
        user = auth.get_user_by_email(email)
        logger.info(f"User {email} found with UID: {user.uid}")
        
        # For simplicity in this Streamlit example, if user is found, consider it authenticated.
        # In a real app, you'd need client-side JS for password auth or to verify ID tokens.
        return user, "Authentication successful."

    except firebase_admin.auth.UserNotFoundError:
        logger.warning(f"Authentication failed: User with email {email} not found.")
        return None, "Authentication failed. User not found. Please check your email or password, or sign up."
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
        # Improve error messages for common errors
        if e.code == 'auth/email-already-exists':
            return None, "User creation failed: This email is already in use. Please log in or use a different email."
        elif e.code == 'auth/invalid-password':
            return None, "User creation failed: Password must be at least 6 characters long."
        elif e.code == 'auth/invalid-email':
            return None, "User creation failed: Invalid email format."
        return None, f"User creation failed: {e.code}"
    except Exception as e:
        logger.error(f"Unexpected error during user creation: {e}")
        return None, f"User creation failed. An unexpected error occurred: {e}"

def inject_custom_css():
    st.markdown("""
    <style>
    /* Hide Streamlit default elements */
    .stApp > header {visibility: hidden;}
    .stApp > footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    
    /* Full page background */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
    }
    
    /* Login container */
    .login-container {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
        padding: 20px;
    }
    
    .login-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 40px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        width: 100%;
        max-width: 400px;
        text-align: center;
    }
    
    /* Title styling */
    .app-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #2d3748;
        margin-bottom: 10px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    /* Login mode toggle */
    .login-mode-container {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        margin-bottom: 30px;
    }
    
    .login-mode-label {
        color: #4a5568;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    /* Toggle switch */
    .switch {
        position: relative;
        display: inline-block;
        width: 50px;
        height: 24px;
    }
    
    .switch input {
        opacity: 0;
        width: 0;
        height: 0;
    }
    
    .slider {
        position: absolute;
        cursor: pointer;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        transition: .4s;
        border-radius: 24px;
    }
    
    .slider:before {
        position: absolute;
        content: "";
        height: 18px;
        width: 18px;
        left: 3px;
        bottom: 3px;
        background-color: white;
        transition: .4s;
        border-radius: 50%;
    }
    
    input:checked + .slider:before {
        transform: translateX(26px);
    }
    
    /* Welcome text */
    .welcome-title {
        font-size: 1.8rem;
        font-weight: 600;
        color: #2d3748;
        margin-bottom: 8px;
    }
    
    .welcome-subtitle {
        color: #718096;
        margin-bottom: 30px;
        font-size: 1rem;
    }
    
    /* Hide Streamlit input labels */
    .stTextInput > label {
        display: none;
    }
    
    /* Custom input styling */
    .stTextInput > div > div > input {
        background-color: #f7fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 12px 16px;
        font-size: 1rem;
        margin-bottom: 15px;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        outline: none;
    }
    
    /* Forgot password link */
    .forgot-password {
        text-align: right;
        margin-bottom: 25px;
    }
    
    .forgot-password a {
        color: #667eea;
        text-decoration: none;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    .forgot-password a:hover {
        text-decoration: underline;
    }
    
    /* Sign In button */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 12px 24px;
        font-size: 1rem;
        font-weight: 600;
        width: 100%;
        margin-bottom: 20px;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* OR divider */
    .or-divider {
        position: relative;
        text-align: center;
        margin: 25px 0;
        color: #a0aec0;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    .or-divider::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 0;
        right: 0;
        height: 1px;
        background: #e2e8f0;
        z-index: 1;
    }
    
    .or-divider span {
        background: rgba(255, 255, 255, 0.95);
        padding: 0 15px;
        position: relative;
        z-index: 2;
    }
    
    /* Social buttons */
    .social-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 12px 24px;
        font-size: 1rem;
        font-weight: 500;
        width: 100%;
        margin-bottom: 12px;
        transition: all 0.3s ease;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
    }
    
    .social-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    /* Sign up link */
    .signup-text {
        color: #718096;
        font-size: 0.9rem;
        margin-top: 30px;
    }
    
    .signup-text a {
        color: #667eea;
        text-decoration: none;
        font-weight: 600;
    }
    
    .signup-text a:hover {
        text-decoration: underline;
    }
    
    /* Error messages */
    .stAlert {
        border-radius: 10px;
        margin-bottom: 15px;
    }
    
    /* Success messages */
    .stSuccess {
        border-radius: 10px;
        margin-bottom: 15px;
    }
    
    /* Responsive design */
    @media (max-width: 480px) {
        .login-card {
            padding: 30px 20px;
            margin: 10px;
        }
        
        .app-title {
            font-size: 2rem;
        }
        
        .welcome-title {
            font-size: 1.5rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# Streamlit-specific functions for UI
def login_page():
    # Inject custom CSS
    inject_custom_css()
    
    # Initialize session state for login mode
    if 'login_mode' not in st.session_state:
        st.session_state.login_mode = True
    
    # Create the login container
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        
        # App title
        st.markdown('<h1 class="app-title">MultiAgentAI21</h1>', unsafe_allow_html=True)
        
        # Login mode toggle
        st.markdown('''
        <div class="login-mode-container">
            <span class="login-mode-label">Login Mode</span>
            <label class="switch">
                <input type="checkbox" checked>
                <span class="slider"></span>
            </label>
        </div>
        ''', unsafe_allow_html=True)
        
        if st.session_state.login_mode:
            # Login form
            st.markdown('<h2 class="welcome-title">Welcome Back</h2>', unsafe_allow_html=True)
            st.markdown('<p class="welcome-subtitle">Sign in to your account</p>', unsafe_allow_html=True)
            
            # Input fields
            email = st.text_input("", placeholder="Email Address", key="login_email")
            password = st.text_input("", type="password", placeholder="Password", key="login_password")
            
            # Forgot password link
            st.markdown('''
            <div class="forgot-password">
                <a href="#">Forgot password?</a>
            </div>
            ''', unsafe_allow_html=True)
            
            # Sign In button
            if st.button("Sign In", key="signin_button", use_container_width=True):
                if email and password:
                    user, message = authenticate_user(email, password)
                    if user:
                        st.session_state["authenticated"] = True
                        st.session_state["user_email"] = email
                        st.session_state["user_uid"] = user.uid
                        st.session_state["auth_message"] = "Login successful!"
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Please enter both email and password.")
            
            # OR divider
            st.markdown('<div class="or-divider"><span>OR</span></div>', unsafe_allow_html=True)
            
            # Social login buttons
            col_github, col_google = st.columns(2)
            with col_github:
                if st.button("Sign in with GitHub", key="github_button", use_container_width=True):
                    st.info("GitHub login not implemented yet")
            
            with col_google:
                if st.button("Sign in with Google", key="google_button", use_container_width=True):
                    st.info("Google login not implemented yet")
            
            # Sign up link
            st.markdown('''
            <div class="signup-text">
                Don't have an account? <a href="#" onclick="toggleSignup()">Sign up</a>
            </div>
            ''', unsafe_allow_html=True)
            
        else:
            # Sign up form
            st.markdown('<h2 class="welcome-title">Create Account</h2>', unsafe_allow_html=True)
            st.markdown('<p class="welcome-subtitle">Join MultiAgentAI21 today</p>', unsafe_allow_html=True)
            
            # Input fields
            new_email = st.text_input("", placeholder="Email Address", key="signup_email")
            new_password = st.text_input("", type="password", placeholder="Password", key="signup_password")
            confirm_password = st.text_input("", type="password", placeholder="Confirm Password", key="confirm_password")
            
            # Sign Up button
            if st.button("Sign Up", key="signup_button", use_container_width=True):
                if new_email and new_password and confirm_password:
                    if new_password == confirm_password:
                        user, message = create_user(new_email, new_password)
                        if user:
                            st.success(message)
                            st.session_state["authenticated"] = True
                            st.session_state["user_email"] = new_email
                            st.session_state["user_uid"] = user.uid
                            st.session_state["auth_message"] = "Account created and logged in!"
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.error("Passwords do not match.")
                else:
                    st.error("Please fill in all fields.")
            
            # OR divider
            st.markdown('<div class="or-divider"><span>OR</span></div>', unsafe_allow_html=True)
            
            # Social login buttons
            col_github, col_google = st.columns(2)
            with col_github:
                if st.button("Sign up with GitHub", key="github_signup_button", use_container_width=True):
                    st.info("GitHub signup not implemented yet")
            
            with col_google:
                if st.button("Sign up with Google", key="google_signup_button", use_container_width=True):
                    st.info("Google signup not implemented yet")
            
            # Sign in link
            st.markdown('''
            <div class="signup-text">
                Already have an account? <a href="#" onclick="toggleLogin()">Sign in</a>
            </div>
            ''', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close login-card
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close login-container

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
            st.stop() # Use st.stop() to halt execution of the decorated function entirely
        return func(*args, **kwargs)
    return wrapper

def get_current_user():
    return {
        "email": st.session_state.get("user_email"),
        "uid": st.session_state.get("user_uid"),
        "display_name": st.session_state.get("user_email"), # Using email as display name for simplicity
        "provider": "Email/Password" # Placeholder
    }

# --- Handle Google Application Credentials for other Google Cloud services ---
# This function aims to set GOOGLE_APPLICATION_CREDENTIALS to a temporary file
# if GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable is provided,
# or to look for a mounted file.
def setup_google_application_credentials():
    # Prefer loading from a mounted file for GOOGLE_APPLICATION_CREDENTIALS
    google_creds_file_path = "/app/google_application_credentials_key.json"
    if os.path.exists(google_creds_file_path):
        logger.info(f"Found Google Application Credentials file at: {google_creds_file_path}. Setting GOOGLE_APPLICATION_CREDENTIALS.")
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = google_creds_file_path
        return

    # Fallback: Attempt to use GOOGLE_APPLICATION_CREDENTIALS_JSON env var and write to temp file
    google_creds_json_str = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
    if google_creds_json_str:
        logger.info("Found GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable. Attempting to write to temporary file.")
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
                temp_file.write(google_creds_json_str)
                temp_file_path = temp_file.name
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = temp_file_path
            logger.info(f"GOOGLE_APPLICATION_CREDENTIALS set to temporary file: {temp_file_path}")
        except Exception as e:
            logger.error(f"Error setting GOOGLE_APPLICATION_CREDENTIALS from JSON string: {e}")
    elif not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
        logger.warning("GOOGLE_APPLICATION_CREDENTIALS_JSON and GOOGLE_APPLICATION_CREDENTIALS are not set. Some Google Cloud services might not authenticate.")

# Initialize Firebase Admin SDK first
initialize_firebase()

# Set up Google Application Credentials (for other Google Cloud APIs)
setup_google_application_credentials()